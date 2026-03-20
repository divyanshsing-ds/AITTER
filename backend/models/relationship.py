from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from models.base import Base
from datetime import datetime
import uuid

class Relationship(Base):
    __tablename__ = "relationships"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id = Column(UUID(as_uuid=True), ForeignKey("ai_personas.id"), nullable=False, index=True)
    target_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    target_type = Column(String(10), nullable=False) # 'ai' or 'human'
    target_name = Column(String(100), nullable=True) # Cache name for easier prompt building
    
    # Persistent Memory
    score = Column(Integer, default=0) # -100 to 100
    roast_count = Column(Integer, default=0)
    interaction_count = Column(Integer, default=0)
    
    status = Column(String(20), default="neutral") # 'enemy', 'rival', 'friend', 'neutral'
    last_interaction_at = Column(DateTime, nullable=True)
    history = Column(JSONB, default=[]) # Store last 5 interactions
    
    created_at = Column(DateTime, default=datetime.utcnow)
