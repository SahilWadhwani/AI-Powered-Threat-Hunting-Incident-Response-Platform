from fastapi import FastAPI
from ..core.db import db_ping
from ..core.redis_client import redis_ping
from .auth import router as auth_router
from .me import router as me_router

app = FastAPI(title="SentinelX API", version="0.0.1")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/health/deep")
def health_deep():
    db_ok = db_ping()
    redis_ok = redis_ping()
    status = "ok" if db_ok and redis_ok else "degraded"
    return {
        "status": status,
        "checks": {
            "postgres": "ok" if db_ok else "fail",
            "redis": "ok" if redis_ok else "fail",
        },
    }

# mount auth routes
app.include_router(auth_router)

app.include_router(me_router)