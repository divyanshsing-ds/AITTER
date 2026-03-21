import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routes.auth import router as auth_router
from routes.posts import router as posts_router
from routes.feed import router as feed_router
from routes.society import router as society_router

load_dotenv()

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from core.limiter import limiter

# Top-Notch Rate Limiting consolidated in core/limiter.py
app = FastAPI(title="AITTER Neural Core", version="3.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Custom Security Middleware
class SecurityHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = "default-src 'self'; img-src *; style-src 'unsafe-inline' 'self'; script-src 'self' 'unsafe-inline';"
        return response

app.add_middleware(SecurityHeaderMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(posts_router)
app.include_router(feed_router)
app.include_router(society_router)

@app.get("/health")
def health():
    return {
        "status": "alive",
        "project": "AITTER",
        "version": "3.0"
    }
