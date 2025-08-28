from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from ..models.block import BlockRule

def utcnow():
    return datetime.now(timezone.utc)

def add_block(db: Session, ip: str, reason: str, created_by: str | None, ttl_minutes: int | None = None) -> BlockRule:
    expires = None
    if ttl_minutes and ttl_minutes > 0:
        expires = utcnow() + timedelta(minutes=ttl_minutes)
    rule = BlockRule(ip=ip, reason=reason, created_by=created_by, expires_at=expires, active=True)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

def list_blocks(db: Session, active_only: bool = True, limit: int = 200, offset: int = 0):
    q = db.query(BlockRule).order_by(BlockRule.id.desc())
    if active_only:
        q = q.filter(BlockRule.active.is_(True))
    return q.limit(limit).offset(offset).all()

def deactivate_block(db: Session, rule_id: int) -> bool:
    r = db.get(BlockRule, rule_id)
    if not r:
        return False
    r.active = False
    db.commit()
    return True

def is_blocked(db: Session, ip: str) -> bool:
    # true if there's an active, non-expired rule
    now = utcnow()
    stmt = select(BlockRule).where(
        BlockRule.ip == ip,
        BlockRule.active.is_(True),
    )
    rows = db.execute(stmt).scalars().all()
    for r in rows:
        if r.expires_at is None or r.expires_at > now:
            return True
    return False