from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from ..core.deps import get_db
from ..core.auth_deps import require_roles
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
def block_ip(
    req: BlockRequest,
    db: Session = Depends(get_db),
    user=Depends(require_roles("analyst", "admin")),
):
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
    user=Depends(require_roles("analyst", "admin")),
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
def unblock(
    block_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_roles("analyst", "admin")),
):
    """
    Deactivate a block rule (JSON body not required).
    """
    ok = deactivate_block(db, block_id)
    if not ok:
        raise HTTPException(status_code=404, detail="block not found")
    return {"ok": True}