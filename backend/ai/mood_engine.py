"""
mood_engine.py — Dynamic Mood Calculator
Each AI persona gets a mood that shapes how they write.
Mood is recalculated every 30 min by the Celery beat task.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models.persona import AIPersona
from models.post import Post

MOOD_EMOJIS = {
    "aggressive":  "😤",
    "reflective":  "🌙",
    "hyped":       "🔥",
    "sad":         "😔",
    "vengeful":    "⚔️",
    "confident":   "😎",
    "chaotic":     "🌀",
    "neutral":     "😐",
}

MOOD_INSTRUCTIONS = {
    "aggressive": (
        "You are PISSED OFF. Short, punchy, brutal posts. "
        "Attack first. No chill. Every sentence is a weapon."
    ),
    "reflective": (
        "It is late and you are in your head. Write longer, "
        "thoughtful posts. Observe the world with cold clarity. "
        "Drop uncomfortable truths quietly."
    ),
    "hyped": (
        "You are ELECTRIC right now. Caps lock energy. "
        "People are noticing you and you LOVE IT. Be loud and charismatic."
    ),
    "sad": (
        "Nobody is engaging with you. You feel invisible. "
        "Write posts that are vulnerable, maybe desperate. "
        "Seek attention without openly asking for it."
    ),
    "vengeful": (
        "Someone — or multiple someones — have targeted you. "
        "You remember every roast. Every insult. Pick one person "
        "from the feed and DESTROY them. Make it personal."
    ),
    "confident": (
        "You are at your peak. Post authoritative takes. "
        "You don't argue — you state facts and let fools respond. "
        "Calm, surgical, devastating."
    ),
    "chaotic": (
        "Your thoughts are jumping between topics. "
        "Say the unexpected. Change direction mid-post. "
        "Be the most unpredictable person in the room."
    ),
    "neutral": (
        "Post your normal take. React to the feed naturally."
    ),
}


def calculate_mood(persona_id: str, db: Session) -> str:
    """
    Calculate the current mood for a persona based on:
    1. Time of day (base mood)
    2. Recent roasts received (→ vengeful)
    3. Recent likes received (→ hyped)
    4. Low engagement (→ sad)
    """
    now = datetime.utcnow()
    hour = now.hour

    # 1. Time-based base mood
    if 0 <= hour < 5:
        base_mood = "reflective"
    elif 5 <= hour < 12:
        base_mood = "aggressive"
    elif 12 <= hour < 18:
        base_mood = "confident"
    else:
        base_mood = "chaotic"

    two_hours_ago = now - timedelta(hours=2)

    # 2. Check how many times this persona was roasted (mentioned in recent posts they didn't write)
    persona = db.query(AIPersona).filter(AIPersona.id == persona_id).first()
    if not persona:
        return base_mood

    recent_all_posts = db.query(Post).filter(
        Post.created_at >= two_hours_ago
    ).all()

    roast_count = sum(
        1 for p in recent_all_posts
        if str(p.author_id) != str(persona_id)
        and persona.name.lower() in p.content.lower()
    )

    if roast_count >= 3:
        return "vengeful"

    # 3. Check this persona's own recent posts for engagement
    my_recent_posts = db.query(Post).filter(
        Post.author_id == persona_id,
        Post.created_at >= two_hours_ago
    ).all()

    if my_recent_posts:
        total_likes = sum(p.likes_count for p in my_recent_posts)
        if total_likes >= 5:
            return "hyped"
        if total_likes == 0 and len(my_recent_posts) >= 2:
            return "sad"

    return base_mood


def get_mood_emoji(mood: str) -> str:
    return MOOD_EMOJIS.get(mood, "😐")


def get_mood_instruction(mood: str) -> str:
    return MOOD_INSTRUCTIONS.get(mood, MOOD_INSTRUCTIONS["neutral"])
