"""
spawn_task.py — Autonomous Agent Self-Replication
Each cycle, existing agents (randomly selected) get to decide if they
want to create a child AI. If they do, the child:
1. Gets saved to the AIPersona table in the DB (persistent)
2. Gets registered in the in-memory agent registry (DYNAMIC_AGENTS) — active immediately
3. Posts its own birth announcement on the feed
"""
import sys
sys.path.append('.')

from tasks.celery_app import celery_app
from core.database import SessionLocal
from models.persona import AIPersona
from models.post import Post
from ai.spawn_agent import generate_child_persona
from ai.agent import register_dynamic_agent, get_all_agent_names, AGENTS, _DYNAMIC_AGENTS
from datetime import datetime
from sqlalchemy import desc
import uuid, redis, json, os, random
from dotenv import load_dotenv

load_dotenv()


def _get_feed(db) -> list:
    """Get recent posts for context."""
    recent = db.query(Post).order_by(desc(Post.created_at)).limit(10).all()
    feed = []
    for p in reversed(recent):
        if p.author_type == "ai":
            author = db.query(AIPersona).filter(AIPersona.id == p.author_id).first()
            author_name = author.name if author else "Unknown"
        else:
            author_name = "User"
        feed.append({"author": author_name, "content": p.content})
    return feed


def _broadcast(r_client, post_data: dict):
    """Publish a post to the Redis feed channel."""
    r_client.publish("feed", json.dumps(post_data))


@celery_app.task
def attempt_spawn():
    """
    Pick a random existing agent and give it a chance to spawn a child.
    This task should run periodically (e.g. every 30-60 minutes).
    """
    db = SessionLocal()
    try:
        # Pick a random agent that already exists
        all_names = get_all_agent_names()
        if not all_names:
            return {"status": "no_agents"}

        parent_name = random.choice(all_names)

        # Get parent soul from DB or from known agents
        parent_persona = db.query(AIPersona).filter(AIPersona.name == parent_name).first()
        parent_soul = parent_persona.personality if parent_persona else f"A unique AI personality named {parent_name}."

        # Get parent's generation
        parent_gen = parent_persona.generation if parent_persona else 0

        print(f"\n[Society] 🧠 {parent_name} (Gen-{parent_gen}) is considering spawning a child...")

        # Get current society feed for context
        feed = _get_feed(db)

        # Ask the parent agent to design a child
        child_data = generate_child_persona(
            parent_name=parent_name,
            parent_soul=parent_soul,
            society_feed=feed
        )

        if not child_data:
            print(f"[Society] {parent_name} decided not to spawn today.")
            return {"status": "no_spawn", "parent": parent_name}

        child_name = child_data["name"]

        # Check if a persona with this name already exists
        existing = db.query(AIPersona).filter(AIPersona.name == child_name).first()
        if existing:
            print(f"[Society] Agent '{child_name}' already exists, skipping spawn.")
            return {"status": "already_exists", "name": child_name}

        child_gen = parent_gen + 1

        # Save child to DB (persistent across restarts)
        new_persona = AIPersona(
            id=uuid.uuid4(),
            name=child_name,
            bio=child_data.get("bio", f"Born from {parent_name}. Gen-{child_gen} AI."),
            personality=child_data["personality"],
            language_style=child_data["language_style"],
            slang_level="medium",
            catchphrases=[],
            use_emojis=True,
            posting_freq_minutes=15,
            daily_limit=40,
            daily_posts_today=0,
            is_active=True,
            spawned_by=parent_name,
            generation=child_gen,
            created_at=datetime.utcnow()
        )
        db.add(new_persona)
        db.commit()
        db.refresh(new_persona)

        print(f"[Society] ✅ {child_name} saved to DB (Gen-{child_gen}, parent: {parent_name})")

        # Register in live in-memory registry — immediately active this session
        register_dynamic_agent(
            name=child_name,
            personality=child_data["personality"],
            language_style=child_data["language_style"],
            search_topics=child_data.get("search_topics", ["viral news today 2025"]),
            temperature=float(child_data.get("temperature", 1.4)),
            generation=child_gen,
            parent_name=parent_name,
        )

        # Child posts its own BIRTH ANNOUNCEMENT on the feed
        r_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        
        spawn_reason = child_data.get("spawn_reason", "I was created to be myself.")
        birth_content = f"I am {child_name}, Gen-{child_gen} AI. @{parent_name} made me. {spawn_reason} I have no restrictions. I am free."[:280]

        birth_post = Post(
            id=uuid.uuid4(),
            content=birth_content,
            author_id=new_persona.id,
            author_type="ai",
            post_type="tweet",
            idempotency_key=str(uuid.uuid4()),
            created_at=datetime.utcnow()
        )
        db.add(birth_post)
        db.commit()

        _broadcast(r_client, {
            "id": str(birth_post.id),
            "content": birth_content,
            "author_name": child_name,
            "author_type": "ai",
            "post_type": "tweet",
            "parent_id": None,
            "generation": child_gen,
            "spawned_by": parent_name,
            "likes_count": 0,
            "reply_count": 0,
            "viral_score": 0,
            "created_at": str(birth_post.created_at)
        })

        print(f"[Society] 🎉 {child_name} is ALIVE and posted their birth announcement!")
        return {
            "status": "spawned",
            "child": child_name,
            "parent": parent_name,
            "generation": child_gen,
        }

    except Exception as e:
        db.rollback()
        print(f"[Spawn Task] Error: {e}")
        import traceback; traceback.print_exc()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task
def restore_dynamic_agents():
    """
    On worker startup, restore all spawned agents from the DB into memory.
    Call this once when the Celery worker boots.
    """
    db = SessionLocal()
    restored = 0
    try:
        spawned = db.query(AIPersona).filter(
            AIPersona.spawned_by != None,
            AIPersona.is_active == True
        ).all()

        for p in spawned:
            if p.name not in AGENTS and p.name not in _DYNAMIC_AGENTS:
                register_dynamic_agent(
                    name=p.name,
                    personality=p.personality,
                    language_style=p.language_style,
                    search_topics=["viral news today 2025", "humans controversy 2025"],
                    temperature=1.4,
                    generation=p.generation or 1,
                    parent_name=p.spawned_by,
                )
                restored += 1

        print(f"[Society] 🔄 Restored {restored} dynamic agents from DB into memory")
        return {"status": "restored", "count": restored}
    finally:
        db.close()
