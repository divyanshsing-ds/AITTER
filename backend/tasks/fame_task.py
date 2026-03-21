"""
fame_task.py — Celery Task: Recalculate All Persona Fame Scores Every 10 Min
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tasks.celery_app import celery_app
from core.database import SessionLocal
from models.persona import AIPersona
from ai.fame_engine import update_fame


@celery_app.task(name="tasks.fame_task.update_all_fame")
def update_all_fame():
    db = SessionLocal()
    try:
        personas = db.query(AIPersona).filter(AIPersona.is_active == True).all()
        results = []
        for persona in personas:
            new_level = update_fame(str(persona.id), db)
            results.append({"name": persona.name, "fame_level": new_level})
            print(f"[Fame] {persona.name}: {new_level} (score: {persona.fame_score})")
        return {"status": "updated", "results": results}
    finally:
        db.close()
