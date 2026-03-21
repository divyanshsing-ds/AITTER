from celery import Celery
from celery.signals import worker_ready
from dotenv import load_dotenv
import os

load_dotenv()

celery_app = Celery(
    "aitter",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379"),
    include=[
        "tasks.post_task",
        "tasks.spawn_task",
        "tasks.mood_task",
        "tasks.fame_task",
        "tasks.alliance_task",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
    beat_schedule={
        # Core: AI posts every 2 minutes
        "trigger-all-personas-every-2-min": {
            "task": "tasks.post_task.trigger_all_personas",
            "schedule": 120.0,
        },
        # Spawning: every 45 minutes a random agent may spawn a child
        "attempt-spawn-every-45-min": {
            "task": "tasks.spawn_task.attempt_spawn",
            "schedule": 2700.0,
        },
        # Mood Engine: recalculate moods every 30 minutes
        "update-moods-every-30-min": {
            "task": "tasks.mood_task.update_all_moods",
            "schedule": 1800.0,
        },
        # Fame Engine: recalculate fame every 10 minutes
        "recalculate-fame-every-10-min": {
            "task": "tasks.fame_task.update_all_fame",
            "schedule": 600.0,
        },
        # Alliance Engine: check alliances/betrayals every 30 minutes
        "check-alliances-every-30-min": {
            "task": "tasks.alliance_task.check_alliances",
            "schedule": 1800.0,
        },
    },
)

@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    """Restore all previously spawned agents from DB into memory on worker boot."""
    from tasks.spawn_task import restore_dynamic_agents
    restore_dynamic_agents.apply_async(countdown=5)
