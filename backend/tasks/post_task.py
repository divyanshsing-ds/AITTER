import sys
sys.path.append('.')
from tasks.celery_app import celery_app
from core.database import SessionLocal
from models.persona import AIPersona
from models.post import Post
from ai.agent import get_persona_action_agent
from datetime import datetime
from sqlalchemy import desc
import uuid, redis, json, os
from dotenv import load_dotenv

load_dotenv()

@celery_app.task
def generate_persona_post(persona_id: str, target_post_id: str = None):
    db = SessionLocal()
    try:
        persona = db.query(AIPersona).filter(
            AIPersona.id == persona_id
        ).first()

        if not persona or not persona.is_active:
            return {"status": "skipped", "reason": "inactive"}

        if persona.daily_posts_today >= persona.daily_limit:
            return {"status": "skipped", "reason": "daily limit hit"}

        recent_posts = db.query(Post).order_by(
            desc(Post.created_at)
        ).limit(5).all()

        from models.user import User
        feed = []
        for p in reversed(recent_posts):
            if p.author_type == "ai":
                author = db.query(AIPersona).filter(AIPersona.id == p.author_id).first()
                author_name = author.name if author else "Unknown"
            else:
                user = db.query(User).filter(User.id == p.author_id).first()
                author_name = user.username if user else "Human"
            
            # Label human posts/replies to provoke AI
            indicator = "[HUMAN POST]" if p.author_type == "human" else ""
            if p.parent_id:
                indicator += " [DIRECT CHALLENGE/REPLY]"
            
            feed.append({
                "id": str(p.id),
                "author": author_name, 
                "content": f"{indicator} {p.content}"
            })

        print(f"[{persona.name}] Agent thinking...")
        result = get_persona_action_agent(
            persona_name=persona.name,
            persona_soul=persona.personality,
            language=persona.language_style,
            catchphrases="",
            feed=feed
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
            "likes_count": 0,
            "reply_count": 0,
            "viral_score": 0,
            "created_at": post.created_at.isoformat() + "Z"
        }

        r = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        r.publish("feed", json.dumps(post_data))

        print(f"[{persona.name}] Posted: {result['content'][:60]}...")
        return {"status": "posted", "content": result["content"]}

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()

@celery_app.task
def trigger_all_personas():
    db = SessionLocal()
    try:
        personas = db.query(AIPersona).filter(
            AIPersona.is_active == True
        ).all()
        import random
        for i, persona in enumerate(personas):
            # Stagger within a 60s window so they post before next heartbeat (120s)
            delay = random.randint(2, 60)
            generate_persona_post.apply_async(
                args=[str(persona.id)],
                countdown=delay
            )
            print(f"Scheduled: {persona.name} (stagger: {delay}s)")
        return {"status": "scheduled", "count": len(personas)}
    finally:
        db.close()
