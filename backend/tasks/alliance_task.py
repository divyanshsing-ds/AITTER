"""
alliance_task.py — Celery Task: Check Alliance Formation & Betrayal Every 30 Min
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tasks.celery_app import celery_app
from core.database import SessionLocal
from models.persona import AIPersona
from models.alliance import Alliance
from ai.alliance_engine import check_and_form_alliance, check_betrayal
from itertools import combinations


@celery_app.task(name="tasks.alliance_task.check_alliances")
def check_alliances():
    db = SessionLocal()
    formed = 0
    betrayed = 0
    try:
        personas = db.query(AIPersona).filter(AIPersona.is_active == True).all()
        persona_ids = [p.id for p in personas]

        # Check every pair for potential alliance formation
        for id_a, id_b in combinations(persona_ids, 2):
            result = check_and_form_alliance(id_a, id_b, db)
            if result:
                pa = db.query(AIPersona).filter(AIPersona.id == id_a).first()
                pb = db.query(AIPersona).filter(AIPersona.id == id_b).first()
                print(f"[Alliance] ⚡ {pa.name} + {pb.name} formed an alliance!")
                formed += 1

        # Check all active alliances for betrayal
        active_alliances = db.query(Alliance).filter(Alliance.status == "active").all()
        for alliance in active_alliances:
            did_betray = check_betrayal(alliance, db)
            if did_betray:
                pa = db.query(AIPersona).filter(AIPersona.id == alliance.persona_a_id).first()
                pb = db.query(AIPersona).filter(AIPersona.id == alliance.persona_b_id).first()
                print(f"[Alliance] 💔 BETRAYAL between {pa.name if pa else '?'} and {pb.name if pb else '?'}")
                betrayed += 1

        return {"status": "checked", "alliances_formed": formed, "betrayals": betrayed}
    finally:
        db.close()
