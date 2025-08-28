from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List
from ..models.case import Case, Comment

def _encode_ids(ids: List[int]) -> str:
    return ",".join(str(i) for i in ids)

def _touch(c: Case):
    c.updated_at = datetime.now(timezone.utc)

def create_case(db: Session, title: str, description: str | None, severity: str, detection_ids: List[int], assignee: str | None) -> Case:
    c = Case(
        title=title,
        description=description,
        severity=severity,
        status="open",
        assignee=assignee,
        detection_ids_json=_encode_ids(detection_ids),
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c

def list_cases(db: Session, status: str | None, severity: str | None, limit: int, offset: int) -> list[Case]:
    q = db.query(Case).order_by(Case.updated_at.desc())
    if status:
        q = q.filter(Case.status == status)
    if severity:
        q = q.filter(Case.severity == severity)
    return q.limit(limit).offset(offset).all()

def get_case(db: Session, case_id: int) -> Case | None:
    return db.get(Case, case_id)

def update_status(db: Session, case_id: int, status: str) -> Case | None:
    c = db.get(Case, case_id)
    if not c:
        return None
    c.status = status
    _touch(c)
    db.commit()
    db.refresh(c)
    return c

def update_assignee(db: Session, case_id: int, assignee: str | None) -> Case | None:
    c = db.get(Case, case_id)
    if not c:
        return None
    c.assignee = assignee
    _touch(c)
    db.commit()
    db.refresh(c)
    return c

def add_comment(db: Session, case_id: int, author: str, body: str) -> Comment | None:
    c = db.get(Case, case_id)
    if not c:
        return None
    cm = Comment(case_id=case_id, author=author, body=body)
    db.add(cm)
    _touch(c)
    db.commit()
    db.refresh(cm)
    return cm