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

router = APIRouter(prefix="/posts", tags=["posts"])

class CreatePostRequest(BaseModel):
    content: str

@router.get("/feed")
def get_feed(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    posts = db.query(Post).order_by(desc(Post.created_at)).offset(skip).limit(limit).all()
    
    result = []
    for post in posts:
        if post.author_type == "ai":
            author = db.query(AIPersona).filter(AIPersona.id == post.author_id).first()
            author_name = author.name if author else "Unknown AI"
        else:
            author = db.query(User).filter(User.id == post.author_id).first()
            author_name = author.username if author else "Unknown User"
        
        result.append({
            "id": str(post.id),
            "content": post.content,
            "author_name": author_name,
            "author_type": post.author_type,
            "post_type": post.post_type,
            "parent_id": str(post.parent_id) if post.parent_id else None,
            "likes_count": post.likes_count,
            "reply_count": post.reply_count,
            "viral_score": post.viral_score,
            "created_at": str(post.created_at)
        })
    
    return {"posts": result, "count": len(result)}

@router.post("/like/{post_id}")
def like_post(post_id: str, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.likes_count += 1
    post.viral_score = (post.likes_count * 1) + (post.reply_count * 2) + (post.quote_count * 3)
    db.commit()
    return {"liked": True, "likes_count": post.likes_count}
