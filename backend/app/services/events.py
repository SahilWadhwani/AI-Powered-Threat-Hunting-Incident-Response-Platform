from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from datetime import datetime
from dateutil import parser as dateparser

from ..models.event import EventNormalized
from ..schemas.events import EventIn
from .enrich import country_for_ip   # <— add

def _parse_timestamp(ts: str) -> datetime:
    # accept ISO8601 and common formats; ensure tz-aware
    dt = dateparser.parse(ts)
    if dt.tzinfo is None:
        # treat naive as UTC
        dt = dt.replace(tzinfo=dateparser.tz.UTC)
    return dt

def normalize_event(e: EventIn) -> EventNormalized:
    country = e.country or country_for_ip(e.src_ip)  # <— enrich if missing
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
        country=country,
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


def list_events(
    db: Session,
    event_module: Optional[str] = None,
    event_action: Optional[str] = None,
    src_ip: Optional[str] = None,
    user: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[EventNormalized]:
    """Return events with optional filters."""

    q = select(EventNormalized)

    conditions = []
    if event_module:
        conditions.append(EventNormalized.event_module == event_module)
    if event_action:
        conditions.append(EventNormalized.event_action == event_action)
    if src_ip:
        conditions.append(EventNormalized.src_ip == src_ip)
    if user:
        conditions.append(EventNormalized.user == user)
    if start:
        try:
            conditions.append(EventNormalized.timestamp >= datetime.fromisoformat(start))
        except Exception:
            pass
    if end:
        try:
            conditions.append(EventNormalized.timestamp <= datetime.fromisoformat(end))
        except Exception:
            pass

    if conditions:
        q = q.where(and_(*conditions))

    q = q.order_by(EventNormalized.id.desc()).limit(limit).offset(offset)

    return db.execute(q).scalars().all()