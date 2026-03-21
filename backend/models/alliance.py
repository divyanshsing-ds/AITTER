from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from models.base import Base
from datetime import datetime
import uuid


class Alliance(Base):
    __tablename__ = "alliances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_a_id = Column(UUID(as_uuid=True), ForeignKey("ai_personas.id"), nullable=False, index=True)
    persona_b_id = Column(UUID(as_uuid=True), ForeignKey("ai_personas.id"), nullable=False, index=True)
    status = Column(String(20), default="active")  # active, broken, betrayed
    formed_at = Column(DateTime, default=datetime.utcnow)
    broken_at = Column(DateTime, nullable=True)
    betrayer_id = Column(UUID(as_uuid=True), nullable=True)
    agreement_count = Column(Integer, default=0)
