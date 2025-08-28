from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from ..core.deps import get_db
from ..core.auth_deps import get_current_user
from ..services.respond import add_block, list_blocks, deactivate_block

router = APIRouter(prefix="/respond", tags=["respond"])

@router.post("/block_ip")
def block_ip(
    ip: str,
    reason: str,
    ttl_minutes: Optional[int] = None,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    if not ip:
        raise HTTPException(status_code=400, detail="ip required")
    rule = add_block(db, ip=ip, reason=reason, created_by=user.email, ttl_minutes=ttl_minutes)
    return {
        "id": rule.id,
        "ip": rule.ip,
        "reason": rule.reason,
        "active": rule.active,
        "expires_at": rule.expires_at,
        "created_by": rule.created_by,
        "created_at": rule.created_at,
    }

@router.get("/blocklist")
def blocklist(
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
    active_only: bool = True,
    limit: int = 200,
    offset: int = 0,
):
    rows = list_blocks(db, active_only=active_only, limit=limit, offset=offset)
    return [
        {
            "id": r.id,
            "ip": r.ip,
            "reason": r.reason,
            "active": r.active,
            "expires_at": r.expires_at,
            "created_by": r.created_by,
            "created_at": r.created_at,
        }
        for r in rows
    ]

@router.post("/unblock")
def unblock(rule_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    ok = deactivate_block(db, rule_id)
    if not ok:
        raise HTTPException(status_code=404, detail="rule not found")
    return {"ok": True}