from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from models.base import Base
from datetime import datetime
import uuid

class Post(Base):
    __tablename__ = "posts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(String(280), nullable=False)
    author_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    author_type = Column(String(10), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("posts.id"), nullable=True, index=True)
    post_type = Column(String(10), default="tweet")
    likes_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)
    quote_count = Column(Integer, default=0)
    viral_score = Column(Integer, default=0, index=True)
    idempotency_key = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
