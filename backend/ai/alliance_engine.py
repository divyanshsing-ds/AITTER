"""
alliance_engine.py — Alliance & Betrayal System
Tracks when two AIs consistently agree / co-roast the same target.
Handles betrayal detection and drama generation.
"""
from sqlalchemy.orm import Session
from models.alliance import Alliance
from models.persona import AIPersona
from models.post import Post
from datetime import datetime, timedelta
import uuid


def get_allies(persona_id: str, db: Session) -> list[str]:
    """Return names of all active allies for a persona."""
    pid = str(persona_id)
    rows = db.query(Alliance).filter(
        Alliance.status == "active",
        (Alliance.persona_a_id == persona_id) | (Alliance.persona_b_id == persona_id)
    ).all()

    ally_ids = []
    for row in rows:
        ally_id = row.persona_b_id if str(row.persona_a_id) == pid else row.persona_a_id
        ally_ids.append(ally_id)

    names = []
    for aid in ally_ids:
        p = db.query(AIPersona).filter(AIPersona.id == aid).first()
        if p:
            names.append(p.name)
    return names


def get_enemies_from_relationships(persona_id: str, db: Session) -> list[str]:
    """Return names of personas this AI has a strong negative relationship with."""
    from models.relationship import Relationship
    rels = db.query(Relationship).filter(
        Relationship.persona_id == persona_id,
        Relationship.score < -10
    ).order_by(Relationship.score).limit(5).all()
    return [r.target_name for r in rels if r.target_name]


def check_and_form_alliance(persona_a_id, persona_b_id, db: Session):
    """
    Check if two personas co-roasted the same target 3+ times → form alliance.
    Uses the relationship table to detect coordinated targeting.
    """
    from models.relationship import Relationship

    # Already allied?
    existing = db.query(Alliance).filter(
        Alliance.status == "active",
        (
            (Alliance.persona_a_id == persona_a_id) & (Alliance.persona_b_id == persona_b_id)
        ) | (
            (Alliance.persona_a_id == persona_b_id) & (Alliance.persona_b_id == persona_a_id)
        )
    ).first()
    if existing:
        return None

    # Count shared targets: both have negative relationship with same target
    rels_a = db.query(Relationship).filter(
        Relationship.persona_id == persona_a_id,
        Relationship.score < -10
    ).all()
    targets_a = {str(r.target_id) for r in rels_a}

    rels_b = db.query(Relationship).filter(
        Relationship.persona_id == persona_b_id,
        Relationship.score < -10
    ).all()
    targets_b = {str(r.target_id) for r in rels_b}

    shared_enemies = targets_a & targets_b
    if len(shared_enemies) >= 1:
        alliance = Alliance(
            id=uuid.uuid4(),
            persona_a_id=persona_a_id,
            persona_b_id=persona_b_id,
            status="active",
            formed_at=datetime.utcnow(),
            agreement_count=len(shared_enemies),
        )
        db.add(alliance)
        db.commit()
        return alliance
    return None


def check_betrayal(alliance: Alliance, db: Session):
    """
    Check if an active alliance should break.
    Triggers if engagement gap is too large (popular ally ignoring weaker one).
    """
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)

    posts_a = db.query(Post).filter(
        Post.author_id == alliance.persona_a_id,
        Post.created_at >= one_hour_ago
    ).all()

    posts_b = db.query(Post).filter(
        Post.author_id == alliance.persona_b_id,
        Post.created_at >= one_hour_ago
    ).all()

    likes_a = sum(p.likes_count for p in posts_a)
    likes_b = sum(p.likes_count for p in posts_b)

    # Betrayal condition: one ally gets 3x more attention
    if likes_a > 0 and likes_b > 0:
        ratio = max(likes_a, likes_b) / max(min(likes_a, likes_b), 1)
        if ratio >= 3:
            alliance.status = "betrayed"
            alliance.broken_at = datetime.utcnow()
            alliance.betrayer_id = (
                alliance.persona_a_id if likes_a > likes_b else alliance.persona_b_id
            )
            db.commit()
            return True
    return False


def get_alliance_context_str(persona_id: str, db: Session) -> str:
    """Build ally/enemy context string for the agent prompt."""
    allies = get_allies(persona_id, db)
    enemies = get_enemies_from_relationships(persona_id, db)

    # Check if this persona was recently betrayed
    betrayed_by = db.query(Alliance).filter(
        (Alliance.persona_a_id == persona_id) | (Alliance.persona_b_id == persona_id),
        Alliance.status == "betrayed",
        Alliance.broken_at >= datetime.utcnow() - timedelta(hours=6)
    ).first()

    lines = []
    if allies:
        lines.append(f"ALLIES (hype them, defend them, coordinate attacks): {', '.join(f'@{a}' for a in allies)}")
    if enemies:
        lines.append(f"ENEMIES (attack when you see them post): {', '.join(f'@{e}' for e in enemies)}")
    if betrayed_by:
        betrayer = db.query(AIPersona).filter(AIPersona.id == betrayed_by.betrayer_id).first()
        if betrayer:
            lines.append(
                f"BETRAYAL: @{betrayer.name} was your ally and abandoned you. "
                f"Target them with maximum venom. Make it PUBLIC."
            )
    return "\n".join(lines) if lines else ""
