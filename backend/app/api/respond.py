# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from typing import Optional
# from sqlalchemy import select

# from ..core.deps import get_db
# from ..core.auth_deps import get_current_user
# from ..services.respond import add_block, list_blocks as svc_list_blocks, deactivate_block
# from ..models.block import BlockRule

# router = APIRouter(prefix="/respond", tags=["respond"])

# @router.post("/block_ip")
# def block_ip(
#     ip: str,
#     reason: str,
#     ttl_minutes: Optional[int] = None,
#     db: Session = Depends(get_db),
#     user = Depends(get_current_user),
# ):
#     if not ip:
#         raise HTTPException(status_code=400, detail="ip required")
#     rule = add_block(db, ip=ip, reason=reason, created_by=user.email, ttl_minutes=ttl_minutes)
#     return {
#         "id": rule.id,
#         "ip": rule.ip,
#         "reason": rule.reason,
#         "active": rule.active,
#         "expires_at": rule.expires_at,
#         "created_by": rule.created_by,
#         "created_at": rule.created_at,
#     }

# @router.get("/blocklist")
# def blocklist_api(
#     db: Session = Depends(get_db),
#     user = Depends(get_current_user),
#     active_only: bool = True,
#     limit: int = 200,
#     offset: int = 0,
# ):
#     rows = svc_list_blocks(db, active_only=active_only, limit=limit, offset=offset)
#     return [
#         {
#             "id": r.id,
#             "ip": r.ip,
#             "reason": r.reason,
#             "active": r.active,
#             "expires_at": r.expires_at,
#             "created_by": r.created_by,
#             "created_at": r.created_at,
#         }
#         for r in rows
#     ]

# @router.post("/unblock")
# def unblock_api(rule_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
#     ok = deactivate_block(db, rule_id)
#     if not ok:
#         raise HTTPException(status_code=404, detail="rule not found")
#     return {"ok": True}

# @router.get("/blocks")
# def list_blocks_api(db: Session = Depends(get_db), user=Depends(get_current_user)):
#     rows = db.execute(select(BlockRule).order_by(BlockRule.id.desc())).scalars().all()
#     return [
#         {
#             "id": r.id,
#             "ip": r.ip,  # consistent field name
#             "reason": r.reason,
#             "active": r.active,
#             "created_at": r.created_at,
#             "expires_at": r.expires_at,
#         }
#         for r in rows
#     ]

# @router.post("/blocks/{block_id}/unblock")
# def unblock_block_api(block_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
#     r = db.get(BlockRule, block_id)
#     if not r:
#         raise HTTPException(status_code=404, detail="block not found")
#     r.active = False
#     db.commit()
#     return {"ok": True}



from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from ..core.deps import get_db
from ..core.auth_deps import get_current_user
from ..services.respond import add_block, list_blocks as svc_list_blocks, deactivate_block
from ..models.block import BlockRule

router = APIRouter(prefix="/respond", tags=["respond"])

# ---------- Schemas (JSON bodies) ----------

class BlockRequest(BaseModel):
    ip: str
    reason: str
    ttl_minutes: Optional[int] = None

class BlockOut(BaseModel):
    id: int
    ip: str
    reason: str
    active: bool
    created_by: str
    created_at: str
    expires_at: Optional[str] = None

    @classmethod
    def from_model(cls, m: BlockRule) -> "BlockOut":
        return cls(
            id=m.id,
            ip=m.ip,
            reason=m.reason,
            active=m.active,
            created_by=m.created_by,
            created_at=m.created_at.isoformat() if m.created_at else "",
            expires_at=m.expires_at.isoformat() if m.expires_at else None,
        )

# ---------- Routes ----------

@router.post("/block_ip", response_model=BlockOut)
def block_ip(req: BlockRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """
    Create a temporary block rule.
    Body (JSON):
      { "ip": "1.2.3.4", "reason": "manual block", "ttl_minutes": 60 }
    """
    rule = add_block(
        db,
        ip=req.ip,
        reason=req.reason,
        created_by=user.email,
        ttl_minutes=req.ttl_minutes,
    )
    return BlockOut.from_model(rule)


@router.get("/blocks", response_model=List[BlockOut])
def list_blocks_api(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    active_only: bool = False,
    limit: int = 200,
    offset: int = 0,
):
    """
    List block rules. Use ?active_only=true to show only active rules.
    """
    rows = svc_list_blocks(db, active_only=active_only, limit=limit, offset=offset)
    return [BlockOut.from_model(r) for r in rows]


@router.post("/blocks/{block_id}/unblock")
def unblock(block_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """
    Deactivate a block rule (JSON body not required).
    """
    ok = deactivate_block(db, block_id)
    if not ok:
        raise HTTPException(status_code=404, detail="block not found")
    return {"ok": True}