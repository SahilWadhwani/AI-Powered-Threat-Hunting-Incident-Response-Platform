from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from ..core.deps import get_db
from ..models.event import EventNormalized
from ..services.enrich import country_for_ip

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