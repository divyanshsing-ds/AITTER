from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import redis, json, asyncio
from dotenv import load_dotenv
import os

load_dotenv()
router = APIRouter(prefix="/feed", tags=["feed"])

@router.get("/stream")
async def feed_stream():
    async def event_generator():
        r = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        pubsub = r.pubsub()
        pubsub.subscribe("feed")
        try:
            while True:
                message = pubsub.get_message(timeout=1.0)
                if message and message["type"] == "message":
                    yield f"data: {message['data'].decode()}\n\n"
                await asyncio.sleep(0.1)
        except Exception:
            pass
        finally:
            pubsub.unsubscribe("feed")
            pubsub.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )
