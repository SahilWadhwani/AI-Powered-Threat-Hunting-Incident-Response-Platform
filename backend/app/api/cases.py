from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from ..core.deps import get_db
from ..core.auth_deps import get_current_user
from ..schemas.cases import CaseCreate, CaseOut
from ..services.cases import create_case, list_cases, get_case, update_status, update_assignee, add_comment
from pydantic import BaseModel

router = APIRouter(prefix="/cases", tags=["cases"])

class CommentIn(BaseModel):
    body: str

@router.post("", response_model=CaseOut, status_code=201)
def create_case_api(payload: CaseCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    c = create_case(db, payload.title, payload.description, payload.severity, payload.detection_ids, payload.assignee or user.email)
    return CaseOut(id=c.id, title=c.title, severity=c.severity, status=c.status, assignee=c.assignee)

@router.get("")
def list_cases_api(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    rows = list_cases(db, status, severity, limit, offset)
    return [
        {"id": c.id, "title": c.title, "severity": c.severity, "status": c.status, "assignee": c.assignee, "updated_at": c.updated_at}
        for c in rows
    ]

@router.get("/{case_id}")
def get_case_api(case_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    c = get_case(db, case_id)
    if not c:
        raise HTTPException(status_code=404, detail="case not found")
    return {
        "id": c.id,
        "title": c.title,
        "description": c.description,
        "severity": c.severity,
        "status": c.status,
        "assignee": c.assignee,
        "detection_ids": [int(x) for x in c.detection_ids_json.split(",")] if c.detection_ids_json else [],
        "created_at": c.created_at,
        "updated_at": c.updated_at,
        "comments": [
            {"id": cm.id, "author": cm.author, "created_at": cm.created_at, "body": cm.body}
            for cm in c.comments
        ],
    }

@router.post("/{case_id}/status")
def set_status(case_id: int, new_status: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    c = update_status(db, case_id, new_status)
    if not c:
        raise HTTPException(status_code=404, detail="case not found")
    return {"ok": True, "status": c.status}

@router.post("/{case_id}/assignee")
def set_assignee(case_id: int, assignee: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    c = update_assignee(db, case_id, assignee)
    if not c:
        raise HTTPException(status_code=404, detail="case not found")
    return {"ok": True, "assignee": c.assignee}

@router.post("/{case_id}/comment")
def add_comment_api(
    case_id: int,
    payload: CommentIn,  # <-- now expects JSON: {"body": "..."}
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    cm = add_comment(db, case_id, user.email, payload.body)
    if not cm:
        raise HTTPException(status_code=404, detail="case not found")
    return {"ok": True, "comment_id": cm.id}