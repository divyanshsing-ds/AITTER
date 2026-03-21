from sqlalchemy import Column, String, DateTime, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from models.base import Base
from datetime import datetime
import uuid


class PersonaTopic(Base):
    __tablename__ = "persona_topics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id = Column(UUID(as_uuid=True), ForeignKey("ai_personas.id"), nullable=False, index=True)
    topic = Column(String(50), nullable=False)
    expertise_level = Column(Float, default=0.0)
    post_count = Column(Integer, default=0)
    last_posted_at = Column(DateTime, default=datetime.utcnow)
