from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..core.deps import get_db
from ..schemas.events import EventBatchIn
from ..services.events import insert_events

router = APIRouter(prefix="/ingest", tags=["ingest"])

@router.post("/events")
def ingest_events(payload: EventBatchIn, db: Session = Depends(get_db)):
    ok, fail = insert_events(db, payload.events)
    return {"ingested": ok, "failed": fail}