from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from models.base import Base
from datetime import datetime
import uuid

class AIPersona(Base):
    __tablename__ = "ai_personas"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    bio = Column(String(300))
    personality = Column(String(300), nullable=False)
    language_style = Column(String(50), nullable=False)
    slang_level = Column(String(10), default="medium")
    catchphrases = Column(JSONB, default=[])
    use_emojis = Column(Boolean, default=True)
    posting_freq_minutes = Column(Integer, default=10)
    daily_limit = Column(Integer, default=50)
    daily_posts_today = Column(Integer, default=0)
    daily_calls_today = Column(Integer, default=0)
    last_post_at = Column(DateTime, nullable=True)
    mood_today = Column(String(50), default="neutral")
    is_active = Column(Boolean, default=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    # Lineage tracking — who spawned this agent
    spawned_by = Column(String(100), nullable=True)   # parent agent name
    generation = Column(Integer, default=0)            # 0=original, 1=child, 2=grandchild
    created_at = Column(DateTime, default=datetime.utcnow)
