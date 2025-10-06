from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional, List
from pathlib import Path
from ..core.deps import get_db
from ..models.detection import Detection
from ..models.event import EventNormalized
from ..detectors.engine import run_all_rules
from ..core.auth_deps import get_current_user, require_roles

router = APIRouter(prefix="/detections", tags=["detections"])

RULES_DIR = Path(__file__).resolve().parents[1] / "detectors" / "rules"

@router.post("/run")
def run_rules(db: Session = Depends(get_db), user = Depends(require_roles("analyst", "admin"))):
    results = run_all_rules(db, RULES_DIR)
    return {"results": results}

@router.get("")
def list_detections(
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    kind: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    q = db.query(Detection).order_by(Detection.id.desc())
    if status:
        q = q.filter(Detection.status == status)
    if kind:
        q = q.filter(Detection.kind == kind)
    if severity:
        q = q.filter(Detection.severity == severity)
    rows = q.limit(limit).offset(offset).all()
    return [
        {
            "id": d.id,
            "created_at": d.created_at,
            "rule_id": d.rule_id,
            "kind": d.kind,
            "severity": d.severity,
            "title": d.title,
            "summary": d.summary,
            "status": d.status,
            "tags": d.tags,
            "event_ids": d.event_ids,
        }
        for d in rows
    ]

@router.get("/{det_id}")
def get_detection(det_id: int, db: Session = Depends(get_db)):
    det = db.get(Detection, det_id)
    if not det:
        return {"error": "not_found"}

    events = []
    if det.event_ids:
        stmt = (
            select(EventNormalized)
            .where(EventNormalized.id.in_(det.event_ids))
            .order_by(EventNormalized.id.desc())
            .limit(200)
        )
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
        "features": det.features_json,
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