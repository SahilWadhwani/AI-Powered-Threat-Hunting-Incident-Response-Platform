from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone

from ..core.deps import get_db
from ..models.event import EventNormalized
from ..models.detection import Detection
from ..models.block import BlockRule

router = APIRouter(prefix="/metrics", tags=["metrics"])

def _utcnow():
    return datetime.now(timezone.utc)

@router.get("/summary")
def metrics_summary(db: Session = Depends(get_db)):
    now = _utcnow()
    start_24h = now - timedelta(hours=24)

    # counts
    events_24h = db.query(func.count(EventNormalized.id))\
                   .filter(EventNormalized.timestamp >= start_24h).scalar() or 0

    open_detections = db.query(func.count(Detection.id))\
                        .filter(Detection.status == "open").scalar() or 0

    # detections by severity
    rows = db.query(Detection.severity, func.count(Detection.id))\
             .group_by(Detection.severity).all()
    by_sev = {sev or "unknown": cnt for sev, cnt in rows}

    # active blocks
    active_blocks = db.query(func.count(BlockRule.id)).filter(BlockRule.active.is_(True)).scalar() or 0

    # hourly timeseries for events in last 24h
    buckets = []
    for i in range(24):
        t0 = start_24h + timedelta(hours=i)
        t1 = t0 + timedelta(hours=1)
        cnt = db.query(func.count(EventNormalized.id))\
                .filter(EventNormalized.timestamp >= t0, EventNormalized.timestamp < t1).scalar() or 0
        buckets.append({"ts": t0.isoformat(), "count": cnt})

    return {
        "events_last_24h": events_24h,
        "detections_open": open_detections,
        "detections_by_severity": by_sev,
        "blocklist_active": active_blocks,
        "events_hourly_24h": buckets,
        "now": now.isoformat(),
    }