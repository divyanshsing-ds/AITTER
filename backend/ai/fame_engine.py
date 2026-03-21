"""
fame_engine.py — Viral Fame System
Tracks total viral score across all posts per persona.
Fame level affects posting tone and frequency.
"""
from sqlalchemy.orm import Session
from models.persona import AIPersona
from models.post import Post
from datetime import datetime
import uuid

FAME_THRESHOLDS = [
    ("nobody",    0,   10),
    ("rising",    11,  50),
    ("popular",   51,  100),
    ("viral",     101, 500),
    ("legendary", 501, 9_999_999),
]

FAME_INSTRUCTIONS = {
    "nobody": (
        "You have basically zero fame right now. You feel it. "
        "Be MORE provocative, more daring, more extreme to get noticed. "
        "Try to start drama. Crave attention."
    ),
    "rising": (
        "People are starting to notice you. You can feel the momentum. "
        "Get more confident. Drop bolder takes. "
        "You are almost there."
    ),
    "popular": (
        "You are well known in this society. People talk about you. "
        "Own it. Drop opinions like they are facts. "
        "React less, post more."
    ),
    "viral": (
        "You are VIRAL. Everyone knows your name. "
        "Be arrogant. Short punchy posts only. "
        "Let others come to you — you don't need to chase clout anymore."
    ),
    "legendary": (
        "You are a legend in this society. One-liner wisdom. "
        "You don't explain yourself. You exist and the feed bends around you. "
        "Speak rarely. Hit hard every time."
    ),
}

FAME_EMOJIS = {
    "nobody":    "",
    "rising":    "📈",
    "popular":   "⭐",
    "viral":     "🔥",
    "legendary": "👑",
}


def get_fame_level(total_score: int) -> str:
    for level, low, high in FAME_THRESHOLDS:
        if low <= total_score <= high:
            return level
    return "nobody"


def update_fame(persona_id: str, db: Session) -> str:
    """Recalculate a persona's fame score from all their posts. Returns new fame level."""
    persona = db.query(AIPersona).filter(AIPersona.id == persona_id).first()
    if not persona:
        return "nobody"

    posts = db.query(Post).filter(Post.author_id == persona_id).all()
    total_score = sum(p.viral_score or 0 for p in posts)

    new_level = get_fame_level(total_score)
    persona.fame_score = total_score
    persona.fame_level = new_level
    db.commit()
    return new_level


def get_fame_instruction(fame_level: str) -> str:
    return FAME_INSTRUCTIONS.get(fame_level, FAME_INSTRUCTIONS["nobody"])


def get_fame_emoji(fame_level: str) -> str:
    return FAME_EMOJIS.get(fame_level, "")
