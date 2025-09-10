# from fastapi import APIRouter, Depends, Query
# from sqlalchemy.orm import Session
# from sqlalchemy import select, and_
# from typing import Optional, List
# from ..core.deps import get_db
# from ..models.event import EventNormalized
# from ..schemas.events import EventOut

# router = APIRouter(prefix="/events", tags=["events"])

# @router.get("", response_model=List[EventOut])
# def list_events(
#     db: Session = Depends(get_db),
#     module: Optional[str] = Query(None, alias="module"),
#     action: Optional[str] = Query(None, alias="action"),
#     user: Optional[str] = None,
#     src_ip: Optional[str] = None,
#     limit: int = 50,
#     offset: int = 0,
# ):
#     conditions = []
#     if module:
#         conditions.append(EventNormalized.event_module == module)
#     if action:
#         conditions.append(EventNormalized.event_action == action)
#     if user:
#         conditions.append(EventNormalized.user == user)
#     if src_ip:
#         conditions.append(EventNormalized.src_ip == src_ip)

#     stmt = select(EventNormalized).order_by(EventNormalized.id.desc()).limit(limit).offset(offset)
#     if conditions:
#         stmt = stmt.where(and_(*conditions))

#     rows = db.execute(stmt).scalars().all()
#     return [
#         EventOut(
#             id=r.id,
#             event_module=r.event_module,
#             event_action=r.event_action,
#             src_ip=r.src_ip,
#             user=r.user,
#             http_path=r.http_path,
#         )
#         for r in rows
#     ]



# backend/app/api/events.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from ..core.deps import get_db
from ..core.auth_deps import get_current_user
from ..services.events import list_events  # whatever you named it

router = APIRouter(prefix="/events", tags=["events"])

@router.get("")
def list_events_api(
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
    event_module: Optional[str] = None,
    event_action: Optional[str] = None,
    src_ip: Optional[str] = None,
    user_filter: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    rows = list_events(
        db,
        event_module=event_module,
        event_action=event_action,
        src_ip=src_ip,
        user=user_filter,
        start=start,
        end=end,
        limit=limit,
        offset=offset,
    )
    return [
        {
            "id": ev.id,
            "timestamp": ev.timestamp.isoformat(),   # <-- ensure ISO string
            "event_module": ev.event_module,
            "event_action": ev.event_action,
            "src_ip": ev.src_ip,
            "user": ev.user,
            "http_path": ev.http_path,
            "country": ev.country,                   # <-- include country
        }
        for ev in rows
    ]