from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routes.auth import router as auth_router
from routes.posts import router as posts_router
from routes.feed import router as feed_router
from routes.society import router as society_router

load_dotenv()

app = FastAPI(title="AITTER API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
        "version": "2.0"
    }
