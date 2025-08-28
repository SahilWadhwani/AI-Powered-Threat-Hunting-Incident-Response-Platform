from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pathlib import Path
from ..core.deps import get_db
from ..models.detection import Detection
from ..detectors.engine import run_all_rules

router = APIRouter(prefix="/detections", tags=["detections"])

RULES_DIR = Path(__file__).resolve().parents[1] / "detectors" / "rules"

@router.post("/run")
def run_rules(db: Session = Depends(get_db)):
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