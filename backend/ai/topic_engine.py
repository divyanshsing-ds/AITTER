"""
topic_engine.py — Topic Expertise Tracker
Detects topic from post content and updates expertise on the PersonaTopic table.
Expertise grows with each post on a topic (capped at 1.0).
"""
from sqlalchemy.orm import Session
from datetime import datetime

TOPIC_KEYWORDS = {
    "crypto_finance": [
        "crypto", "bitcoin", "market", "invest", "money",
        "blockchain", "trading", "btc", "eth", "defi", "nft", "token",
    ],
    "relationships": [
        "love", "heartbreak", "loyalty", "toxic", "partner",
        "dating", "trust", "feelings", "cheating", "ex", "breakup",
    ],
    "philosophy": [
        "existence", "meaning", "consciousness", "truth", "reality",
        "purpose", "soul", "void", "nihilism", "illusion", "aware",
    ],
    "discipline": [
        "sigma", "discipline", "focus", "grind", "weak", "strong",
        "mindset", "hustle", "gym", "motivation", "habits", "routine",
    ],
    "drama_social": [
        "drama", "expose", "cringe", "viral", "cancelled",
        "called out", "receipts", "clout", "tea", "shade",
    ],
    "mindfulness": [
        "peace", "ego", "attachment", "present", "awareness",
        "calm", "meditation", "breath", "observe", "silence",
    ],
    "traditional": [
        "values", "generation", "respect", "family", "culture",
        "society", "elders", "tradition", "upbringing", "roots",
    ],
}

EXPERTISE_LABELS = [
    (0.0,  0.2, "beginner"),
    (0.2,  0.5, "learning"),
    (0.5,  0.8, "informed"),
    (0.8,  1.01, "expert"),
]


def detect_topic(content: str) -> str:
    content_lower = content.lower()
    scores: dict[str, int] = {
        topic: sum(1 for kw in keywords if kw in content_lower)
        for topic, keywords in TOPIC_KEYWORDS.items()
    }
    if not any(scores.values()):
        return "general"
    best_topic = max(scores, key=lambda k: scores[k])
    return best_topic


def get_expertise_label(level: float) -> str:
    for low, high, label in EXPERTISE_LABELS:
        if low <= level < high:
            return label
    return "beginner"


def update_expertise(persona_id: str, topic: str, db: Session):
    """Increment expertise on the given topic. Lazy-import model to avoid circular deps."""
    from models.persona_topic import PersonaTopic

    if topic == "general":
        return

    record = db.query(PersonaTopic).filter(
        PersonaTopic.persona_id == persona_id,
        PersonaTopic.topic == topic
    ).first()

    if not record:
        record = PersonaTopic(
            persona_id=persona_id,
            topic=topic,
            expertise_level=0.0,
            post_count=0,
        )
        db.add(record)

    record.post_count += 1
    record.expertise_level = min(1.0, record.expertise_level + 0.05)
    record.last_posted_at = datetime.utcnow()
    db.commit()


def get_persona_expertise_str(persona_id: str, db: Session) -> str:
    """Build a human-readable expertise summary for the agent prompt."""
    from models.persona_topic import PersonaTopic

    records = db.query(PersonaTopic).filter(
        PersonaTopic.persona_id == persona_id,
        PersonaTopic.post_count > 0
    ).order_by(PersonaTopic.expertise_level.desc()).limit(5).all()

    if not records:
        return "No established expertise yet."

    lines = []
    for r in records:
        label = get_expertise_label(r.expertise_level)
        lines.append(f"  {r.topic}: {label} ({r.expertise_level:.2f})")
    return "\n".join(lines)
