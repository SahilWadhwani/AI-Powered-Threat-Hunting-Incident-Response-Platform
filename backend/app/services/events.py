from typing import List, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
from dateutil import parser as dateparser

from ..models.event import EventNormalized
from ..schemas.events import EventIn

def _parse_timestamp(ts: str) -> datetime:
    # accept ISO8601 and common formats; ensure tz-aware
    dt = dateparser.parse(ts)
    if dt.tzinfo is None:
        # treat naive as UTC
        dt = dt.replace(tzinfo=dateparser.tz.UTC)
    return dt

def normalize_event(e: EventIn) -> EventNormalized:
    return EventNormalized(
        timestamp=_parse_timestamp(e.timestamp),
        event_module=e.event_module,
        event_action=e.event_action,
        src_ip=e.src_ip,
        dst_ip=e.dst_ip,
        user=e.user,
        http_method=e.http_method,
        http_path=e.http_path,
        user_agent=e.user_agent,
        country=e.country,
        fields_json=e.fields or {},
        raw_ref=e.raw_ref,
    )

def insert_events(db: Session, items: List[EventIn]) -> Tuple[int, int]:
    ok, fail = 0, 0
    for e in items:
        try:
            rec = normalize_event(e)
            db.add(rec)
            ok += 1
        except Exception:
            fail += 1
    db.commit()
    return ok, fail