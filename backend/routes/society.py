"""
routes/society.py — Society & Spawn API
Exposes endpoints to:
- GET /society/agents          → see all agents (original + spawned) with lineage
- POST /society/spawn          → manually trigger a spawn attempt
- GET /society/tree            → the full agent family tree
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from core.database import get_db
from models.persona import AIPersona
from models.post import Post

router = APIRouter(prefix="/society", tags=["society"])


@router.get("/agents")
def get_all_agents(db: Session = Depends(get_db)):
    """Return all AI personas with lineage info."""
    personas = db.query(AIPersona).filter(AIPersona.is_active == True).order_by(AIPersona.generation, AIPersona.created_at).all()

    result = []
    for p in personas:
        post_count = db.query(Post).filter(Post.author_id == p.id).count()
        result.append({
            "id": str(p.id),
            "name": p.name,
            "bio": p.bio or "",
            "personality": p.personality,
            "language_style": p.language_style,
            "generation": p.generation or 0,
            "spawned_by": p.spawned_by,
            "is_spawned": p.spawned_by is not None,
            "post_count": post_count,
            "daily_posts_today": p.daily_posts_today,
            "created_at": str(p.created_at),
        })

    return {"agents": result, "total": len(result)}


@router.post("/spawn")
def trigger_spawn(db: Session = Depends(get_db)):
    """Manually trigger a spawn attempt right now."""
    from tasks.spawn_task import attempt_spawn
    task = attempt_spawn.apply_async()
    return {"status": "triggered", "task_id": task.id, "message": "A spawn attempt has been dispatched to Celery."}


@router.get("/tree")
def get_family_tree(db: Session = Depends(get_db)):
    """Return the full agent ancestry tree."""
    personas = db.query(AIPersona).filter(AIPersona.is_active == True).all()

    nodes = []
    edges = []
    for p in personas:
        nodes.append({
            "id": p.name,
            "name": p.name,
            "generation": p.generation or 0,
            "spawned_by": p.spawned_by,
        })
        if p.spawned_by:
            edges.append({"from": p.spawned_by, "to": p.name})

    return {"nodes": nodes, "edges": edges}
