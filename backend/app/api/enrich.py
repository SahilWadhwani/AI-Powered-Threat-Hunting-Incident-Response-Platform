from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from ..core.deps import get_db
from ..models.event import EventNormalized
from ..services.enrich import country_for_ip
from sqlalchemy import select
from ..models.event import EventNormalized
from ..models.detection import Detection

router = APIRouter(prefix="/enrich", tags=["enrichment"])

@router.post("/geoip/backfill")
def geoip_backfill(hours: int = 24, db: Session = Depends(get_db)):
    # Fill missing country for events in the last N hours
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=hours)

    stmt = select(EventNormalized).where(
        EventNormalized.timestamp >= start,
        EventNormalized.timestamp < end,
        (EventNormalized.country.is_(None)) | (EventNormalized.country == "")
    ).limit(5000)

    rows = db.execute(stmt).scalars().all()
    updated = 0
    for r in rows:
        code = country_for_ip(r.src_ip)
        if code:
            r.country = code
            updated += 1
    if updated:
        db.commit()
    return {"scanned": len(rows), "updated": updated}


@router.get("/{det_id}")
def get_detection(det_id: int, db: Session = Depends(get_db)):
    det = db.get(Detection, det_id)
    if not det:
        return {"error": "not_found"}

    events = []
    if det.event_ids:
        stmt = select(EventNormalized).where(EventNormalized.id.in_(det.event_ids)).order_by(EventNormalized.id.desc()).limit(200)
        events = db.execute(stmt).scalars().all()

    return {
        "id": det.id,
        "created_at": det.created_at,
        "rule_id": det.rule_id,
        "kind": det.kind,
        "severity": det.severity,
        "title": det.title,
        "summary": det.summary,
        "status": det.status,
        "tags": det.tags,
        "event_ids": det.event_ids,
        "evidence_events": [
            {
                "id": e.id,
                "timestamp": e.timestamp,
                "event_module": e.event_module,
                "event_action": e.event_action,
                "src_ip": e.src_ip,
                "user": e.user,
                "http_path": e.http_path,
                "country": e.country,
            }
            for e in events
        ],
    }
