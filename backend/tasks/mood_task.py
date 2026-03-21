"""
mood_task.py — Celery Task: Update All Persona Moods Every 30 Min
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tasks.celery_app import celery_app
from core.database import SessionLocal
from models.persona import AIPersona
from ai.mood_engine import calculate_mood


@celery_app.task(name="tasks.mood_task.update_all_moods")
def update_all_moods():
    db = SessionLocal()
    try:
        personas = db.query(AIPersona).filter(AIPersona.is_active == True).all()
        for persona in personas:
            new_mood = calculate_mood(str(persona.id), db)
            if persona.mood_today != new_mood:
                print(f"[Mood] {persona.name}: {persona.mood_today} → {new_mood}")
                persona.mood_today = new_mood
        db.commit()
        return {"status": "updated", "count": len(personas)}
    finally:
        db.close()
