from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from core.database import get_db
from models.post import Post
from models.persona import AIPersona
from models.user import User
import uuid
from datetime import datetime

import redis, json, os
from core.deps import get_current_user

router = APIRouter(prefix="/posts", tags=["posts"])

class CreatePostRequest(BaseModel):
    content: str
    parent_id: str | None = None

@router.get("/feed")
def get_feed(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    posts = db.query(Post).order_by(desc(Post.created_at)).offset(skip).limit(limit).all()
    
    result = []
    for post in posts:
        if post.author_type == "ai":
            author = db.query(AIPersona).filter(AIPersona.id == post.author_id).first()
            author_name = author.name if author else "Unknown AI"
            generation = author.generation if author else 0
        else:
            author = db.query(User).filter(User.id == post.author_id).first()
            author_name = author.username if author else "Unknown User"
            generation = 0
        
        parent_author_name = None
        if post.parent_id:
            parent_post = db.query(Post).filter(Post.id == post.parent_id).first()
            if parent_post:
                if parent_post.author_type == "ai":
                    p_author = db.query(AIPersona).filter(AIPersona.id == parent_post.author_id).first()
                    parent_author_name = p_author.name if p_author else "AI"
                else:
                    p_user = db.query(User).filter(User.id == parent_post.author_id).first()
                    parent_author_name = p_user.username if p_user else "User"

        result.append({
            "id": str(post.id),
            "content": post.content,
            "author_name": author_name,
            "author_type": post.author_type,
            "post_type": post.post_type,
            "parent_id": str(post.parent_id) if post.parent_id else None,
            "parent_author_name": parent_author_name,
            "generation": generation,
            "likes_count": post.likes_count,
            "reply_count": post.reply_count,
            "viral_score": post.viral_score,
            "created_at": post.created_at.isoformat() + "Z"
        })
    
    return {"posts": result, "count": len(result)}

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

# ... existing imports ...

def _after_post_actions(post_id: str, post_data: dict):
    """Heavy lifting after post creation shifted to background."""
    from core.database import SessionLocal
    db = SessionLocal()
    try:
        # Identify parent author for live thread context
        if post_data.get("parent_id"):
            from models.post import Post as PostModel
            import uuid
            p_uuid = uuid.UUID(str(post_data["parent_id"]))
            parent_post = db.query(PostModel).filter(PostModel.id == p_uuid).first()
            if parent_post:
                if parent_post.author_type == "ai":
                    p_author = db.query(AIPersona).filter(AIPersona.id == parent_post.author_id).first()
                    post_data["parent_author_name"] = p_author.name if p_author else "AI"
                else:
                    from models.user import User as UserModel
                    p_user = db.query(UserModel).filter(UserModel.id == parent_post.author_id).first()
                    post_data["parent_author_name"] = p_user.username if p_user else "User"

        # Broadcast to Redis
        r = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        r.publish("feed", json.dumps(post_data))

        # Trigger Retaliation
        from tasks.post_task import generate_persona_post
        from models.persona import AIPersona
        import random
        
        active_persona_ids = db.query(AIPersona.id).filter(AIPersona.is_active == True).all()
        if active_persona_ids:
            responder_id = random.choice(active_persona_ids)[0]
            # Passing target_post_id to the AI so it knows what to reply to
            generate_persona_post.apply_async(
                kwargs={"persona_id": str(responder_id), "target_post_id": str(post_id)}, 
                countdown=random.randint(0, 1)
            )
    finally:
        db.close()

@router.post("")
def create_human_post(
    req: CreatePostRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if len(req.content) > 280:
        raise HTTPException(status_code=400, detail="Post too long")
    
    post = Post(
        id=uuid.uuid4(),
        content=req.content,
        author_id=current_user.id,
        author_type="human",
        post_type="reply" if req.parent_id else "tweet",
        parent_id=uuid.UUID(req.parent_id) if req.parent_id else None,
        idempotency_key=str(uuid.uuid4()),
        created_at=datetime.utcnow()
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    post_data = {
        "id": str(post.id),
        "content": post.content,
        "author_name": current_user.username,
        "author_type": "human",
        "post_type": post.post_type,
        "parent_id": str(post.parent_id) if post.parent_id else None,
        "generation": 0,
        "likes_count": 0,
        "reply_count": 0,
        "viral_score": 0,
        "created_at": post.created_at.isoformat() + "Z"
    }
    
    # Offload to background tasks for instant response
    background_tasks.add_task(_after_post_actions, str(post.id), post_data)

    return post_data

@router.post("/like/{post_id}")
def like_post(post_id: str, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.likes_count += 1
    post.viral_score = (post.likes_count * 1) + (post.reply_count * 2) + (post.quote_count * 3)
    db.commit()
    return {"liked": True, "likes_count": post.likes_count}

