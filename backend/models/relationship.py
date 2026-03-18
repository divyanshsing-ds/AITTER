from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from models.base import Base
from datetime import datetime
import uuid

class Relationship(Base):
    __tablename__ = "relationships"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_a_id = Column(UUID(as_uuid=True), ForeignKey("ai_personas.id"), nullable=False, index=True)
    persona_b_id = Column(UUID(as_uuid=True), ForeignKey("ai_personas.id"), nullable=False, index=True)
    score_a_to_b = Column(Integer, default=0)
    score_b_to_a = Column(Integer, default=0)
    status = Column(String(10), default="neutral")
    last_interaction_at = Column(DateTime, nullable=True)
    cooldown_until = Column(DateTime, nullable=True)
    inside_jokes = Column(JSONB, default=[])
    history = Column(JSONB, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
