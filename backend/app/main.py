from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.settings import settings
from routers.auth import router as auth_router
from routers.comments import router as comments_router
from routers.feed import router as feed_router
from routers.follows import router as follows_router
from routers.likes import router as likes_router
from routers.tweets import router as tweets_router
from routers.users import router as users_router


app = FastAPI(
    title="Mini-Twitter API",
    description="Twitter-like social media application",
    version="2.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# STATIC FILES
# ============================================================

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(auth_router)
app.include_router(tweets_router)
app.include_router(users_router)
app.include_router(likes_router)
app.include_router(comments_router)
app.include_router(follows_router)
app.include_router(feed_router)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Mini-Twitter API is running!"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }