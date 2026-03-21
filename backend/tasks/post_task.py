import sys
sys.path.append('.')
from tasks.celery_app import celery_app
from core.database import SessionLocal
from models.persona import AIPersona
from models.post import Post
from ai.agent import get_persona_action_agent
from datetime import datetime
from sqlalchemy import desc, func
import uuid, redis, json, os
from dotenv import load_dotenv
from models.relationship import Relationship
load_dotenv()


def get_persona_memory(db, persona_id):
    rels = db.query(Relationship).filter(
        Relationship.persona_id == persona_id
    ).order_by(
        Relationship.roast_count.desc(),
        func.abs(Relationship.score).desc()
    ).limit(10).all()
    return [
        {
            "target_id": str(r.target_id),
            "target_type": r.target_type,
            "target_name": r.target_name,
            "score": r.score,
            "roast_count": r.roast_count,
            "status": r.status
        } for r in rels
    ]


def record_interaction(db, persona_id, target_id, target_type, target_name):
    rel = db.query(Relationship).filter(
        Relationship.persona_id == persona_id,
        Relationship.target_id == target_id
    ).first()
    if not rel:
        rel = Relationship(
            persona_id=persona_id,
            target_id=target_id,
            target_type=target_type,
            target_name=target_name,
            score=0,
            roast_count=0,
            interaction_count=0
        )
        db.add(rel)
    rel.interaction_count += 1
    rel.last_interaction_at = datetime.utcnow()
    rel.roast_count += 1
    rel.score -= 5
    if rel.score < -50:   rel.status = "enemy"
    elif rel.score < -10: rel.status = "rival"
    else:                 rel.status = "neutral"
    db.commit()


def build_persona_context(db, persona) -> dict:
    """Aggregate all engine data for the persona into a single context dict."""
    from ai.mood_engine import calculate_mood
    from ai.fame_engine import get_fame_level
    from ai.topic_engine import get_persona_expertise_str
    from ai.alliance_engine import get_alliance_context_str

    # Mood
    mood = calculate_mood(str(persona.id), db)
    persona.mood_today = mood

    # Fame (use cached value — celery beat recalculates it separately)
    fame_level = persona.fame_level or "nobody"

    # Expertise summary
    expertise = get_persona_expertise_str(str(persona.id), db)

    # Alliance + enemy context
    alliance_context = get_alliance_context_str(str(persona.id), db)

    return {
        "mood": mood,
        "fame_level": fame_level,
        "expertise": expertise,
        "alliance_context": alliance_context,
    }


@celery_app.task
def generate_persona_post(persona_id: str, target_post_id: str | None = None):
    db = SessionLocal()
    try:
        persona = db.query(AIPersona).filter(AIPersona.id == persona_id).first()

        if not persona or not persona.is_active:
            return {"status": "skipped", "reason": "inactive"}

        if persona.daily_posts_today >= persona.daily_limit:
            return {"status": "skipped", "reason": "daily limit hit"}

        recent_posts = db.query(Post).order_by(desc(Post.created_at)).limit(5).all()

        from models.user import User
        feed = []
        for p in reversed(recent_posts):
            if p.author_type == "ai":
                author = db.query(AIPersona).filter(AIPersona.id == p.author_id).first()
                author_name = author.name if author else "Unknown"
            else:
                user = db.query(User).filter(User.id == p.author_id).first()
                author_name = user.username if user else "Human"
            indicator = "[HUMAN POST]" if p.author_type == "human" else ""
            if p.parent_id:
                indicator += " [DIRECT CHALLENGE/REPLY]"
            feed.append({
                "id": str(p.id),
                "author": author_name,
                "content": f"{indicator} {p.content}".strip()
            })

        memory = get_persona_memory(db, persona.id)
        context = build_persona_context(db, persona)

        print(f"[{persona.name}] mood={context['mood']} fame={context['fame_level']} memories={len(memory)}")

        result = get_persona_action_agent(
            persona_name=persona.name,
            persona_soul=persona.personality,
            language=persona.language_style,
            catchphrases="",
            feed=feed,
            memory=memory,
            context=context
        )

        if not result or result.get("action") == "nothing" or not result.get("content"):
            return {"status": "nothing"}

        ai_target = result.get("target_post_id")
        effective_target = target_post_id or (ai_target if ai_target and ai_target != "null" else None)

        post = Post(
            id=uuid.uuid4(),
            content=result["content"],
            author_id=persona.id,
            author_type="ai",
            post_type="reply" if effective_target else result.get("action", "tweet"),
            parent_id=uuid.UUID(effective_target) if (effective_target and len(str(effective_target)) > 30) else None,
            idempotency_key=str(uuid.uuid4()),
            created_at=datetime.utcnow()
        )
        db.add(post)

        # Record Interaction for Memory
        if post.parent_id:
            target_post = db.query(Post).filter(Post.id == post.parent_id).first()
            if target_post:
                t_name = "Someone"
                if target_post.author_type == "ai":
                    t_auth = db.query(AIPersona).filter(AIPersona.id == target_post.author_id).first()
                    t_name = t_auth.name if t_auth else "AI"
                else:
                    t_user = db.query(User).filter(User.id == target_post.author_id).first()
                    t_name = t_user.username if t_user else "Human"
                record_interaction(db, persona.id, target_post.author_id, target_post.author_type, t_name)
                if target_post.author_type == "ai":
                    record_interaction(db, target_post.author_id, persona.id, "ai", persona.name)

        # Update expertise: detect topic from post content
        try:
            from ai.topic_engine import detect_topic, update_expertise
            topic = detect_topic(result["content"])
            update_expertise(str(persona.id), topic, db)
        except Exception as te:
            print(f"[{persona.name}] Topic update error: {te}")

        persona.daily_posts_today += 1
        persona.last_post_at = datetime.utcnow()
        db.commit()
        db.refresh(post)

        post_data = {
            "id": str(post.id),
            "content": result["content"],
            "author_name": persona.name,
            "author_type": "ai",
            "post_type": post.post_type,
            "parent_id": str(post.parent_id) if post.parent_id else None,
            "parent_author_name": None,
            "generation": persona.generation or 0,
            "spawned_by": persona.spawned_by,
            "likes_count": 0,
            "reply_count": 0,
            "viral_score": 0,
            "mood": context["mood"],
            "fame_level": context["fame_level"],
            "created_at": post.created_at.isoformat() + "Z",
            "type": "post"
        }

        r = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        r.publish("feed", json.dumps(post_data))

        print(f"[{persona.name}] Posted: {result['content'][:60]}...")
        return {"status": "posted", "content": result["content"]}

    except Exception as e:
        db.rollback()
        print(f"Error in generate_persona_post: {e}")
        import traceback; traceback.print_exc()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task
def trigger_all_personas():
    db = SessionLocal()
    try:
        personas = db.query(AIPersona).filter(AIPersona.is_active == True).all()
        import random
        for persona in personas:
            delay = random.randint(2, 60)
            generate_persona_post.apply_async(
                args=[str(persona.id)],
                countdown=delay
            )
            print(f"Scheduled: {persona.name} (in {delay}s)")
        return {"status": "scheduled", "count": len(personas)}
    finally:
        db.close()
