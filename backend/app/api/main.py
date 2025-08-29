from fastapi import FastAPI
from ..core.db import db_ping
from ..core.redis_client import redis_ping
from .auth import router as auth_router
from .me import router as me_router
from .ingest import router as ingest_router
from .events import router as events_router
from .detections import router as detections_router
from .enrich import router as enrich_router
from .cases import router as cases_router
from .respond import router as respond_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SentinelX API", version="0.0.1")

# CORS for local Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

app.include_router(ingest_router)
app.include_router(events_router)
app.include_router(detections_router)
app.include_router(enrich_router)
app.include_router(cases_router)
app.include_router(respond_router)