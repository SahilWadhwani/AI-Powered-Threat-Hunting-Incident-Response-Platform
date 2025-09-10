from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

# ⬇️ use absolute import so it works when loaded via importlib
from backend.app.models.event import EventNormalized

NAME = "Geo-Rare-Login"

WINDOW_MIN = 10          # look in the last 10 minutes for new successes
HISTORY_DAYS = 30        # compare to the last 30 days of history (before window)
MODULE = "auth"
ACTION = "ssh_login_success"
MIN_USER_LEN = 1
IGNORE_COUNTRIES = {None, "", "ZZ"}

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

def run(db: Session, since: datetime | None = None, until: datetime | None = None) -> List[Dict[str, Any]]:
    if not until:
        until = _utcnow()
    if not since:
        since = until - timedelta(minutes=WINDOW_MIN)

    ev = EventNormalized

    # 1) successes in the current window
    cur_q = (
        select(ev.user, ev.country, func.array_agg(ev.id).label("ids"))
        .where(
            and_(
                ev.timestamp >= since,
                ev.timestamp <= until,
                ev.event_module == MODULE,
                ev.event_action == ACTION,
                ev.user.isnot(None),
                ev.country.isnot(None),
            )
        )
        .group_by(ev.user, ev.country)
    )
    cur_rows = db.execute(cur_q).all()
    if not cur_rows:
        return []

    # 2) check 30d history for same (user,country)
    hist_end = since
    hist_start = hist_end - timedelta(days=HISTORY_DAYS)

    findings: List[Dict[str, Any]] = []
    for user, country, ids in cur_rows:
        user = (user or "").strip()
        country = (country or "").strip() or None
        if not user or len(user) < MIN_USER_LEN or country in IGNORE_COUNTRIES:
            continue

        hist_q = (
            select(func.count())
            .where(
                and_(
                    ev.timestamp >= hist_start,
                    ev.timestamp < hist_end,
                    ev.event_module == MODULE,
                    ev.event_action == ACTION,
                    ev.user == user,
                    ev.country == country,
                )
            )
        )
        (hist_cnt,) = db.execute(hist_q).first()

        if int(hist_cnt or 0) == 0:
            findings.append({
                "rule_name": NAME,
                "title": f"Suspicious geo login for {user} from {country}",
                "severity": "high",
                "primary_src_ip": None,
                "summary": (
                    f"User '{user}' logged in successfully from new country '{country}' "
                    f"not seen in the past {HISTORY_DAYS}d."
                ),
                "evidence_event_ids": [int(x) for x in (ids or []) if x is not None][:50],
            })
    return findings