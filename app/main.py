from fastapi import FastAPI

from . import models
from .database import Base, engine
from routers.auth import router as auth_router
from routers.tweets import router as tweets_router
from fastapi.staticfiles import StaticFiles
from routers.users import router as users_router

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Mini-Twitter API",
    description="Twitter-like social media application",
    version="2.0.0"
)

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)


app.include_router(auth_router)
app.include_router(tweets_router)
app.include_router(users_router)


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