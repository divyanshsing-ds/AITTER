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
def generate_persona_post(persona_id: str):
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

        feed = []
        for p in reversed(recent_posts):
            if p.author_type == "ai":
                author = db.query(AIPersona).filter(AIPersona.id == p.author_id).first()
                author_name = author.name if author else "Unknown"
            else:
                author_name = "User"
            feed.append({"author": author_name, "content": p.content})

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

        post = Post(
            id=uuid.uuid4(),
            content=result["content"],
            author_id=persona.id,
            author_type="ai",
            post_type=result.get("action", "tweet"),
            idempotency_key=str(uuid.uuid4()),
            created_at=datetime.utcnow()
        )
        db.add(post)
        persona.daily_posts_today += 1
        persona.last_post_at = datetime.utcnow()
        db.commit()

        post_data = {
            "id": str(post.id),
            "content": result["content"],
            "author_name": persona.name,
            "author_type": "ai",
            "post_type": result.get("action", "tweet"),
            "likes_count": 0,
            "reply_count": 0,
            "viral_score": 0,
            "created_at": str(post.created_at)
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
        for i, persona in enumerate(personas):
            generate_persona_post.apply_async(
                args=[str(persona.id)],
                countdown=i * 90
            )
            print(f"Scheduled: {persona.name} (delay: {i*90}s)")
        return {"status": "scheduled", "count": len(personas)}
    finally:
        db.close()
