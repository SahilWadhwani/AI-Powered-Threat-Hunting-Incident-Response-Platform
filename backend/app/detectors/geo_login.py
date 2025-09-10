from __future__ import annotations
from typing import Dict, List, Tuple
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from ..models.event import EventNormalized
from ..models.detection import Detection

RID = "Geo-Rare-Login"
SEVERITY = "medium"

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def run(db: Session) -> int:
    """
    Create a detection when we see an ssh_login_success from a country that
    user hasn't used recently (baseline window).
    """
    now = _now_utc()
    recent_window = now - timedelta(days=1)      # look for successes in last 24h
    baseline_window = now - timedelta(days=14)   # countries seen in last 14d

    # recent successes with a country
    recent_stmt = (
        select(EventNormalized.id,
               EventNormalized.user,
               EventNormalized.country,
               EventNormalized.timestamp)
        .where(
            and_(
                EventNormalized.timestamp >= recent_window,
                EventNormalized.event_module == "auth",
                EventNormalized.event_action == "ssh_login_success",
                EventNormalized.country.is_not(None),
                EventNormalized.user.is_not(None),
            )
        )
        .order_by(EventNormalized.id.desc())
    )
    recent = db.execute(recent_stmt).all()

    if not recent:
        return 0

    # build per-user baseline of countries in the last 14d (excluding last 24h so it doesn't “learn” immediately)
    baseline_stmt = (
        select(EventNormalized.user, EventNormalized.country)
        .where(
            and_(
                EventNormalized.timestamp >= baseline_window,
                EventNormalized.timestamp < recent_window,
                EventNormalized.event_module == "auth",
                EventNormalized.event_action == "ssh_login_success",
                EventNormalized.country.is_not(None),
                EventNormalized.user.is_not(None),
            )
        )
        .group_by(EventNormalized.user, EventNormalized.country)
    )
    baseline_rows = db.execute(baseline_stmt).all()

    baseline: Dict[str, set] = {}
    for user, country in baseline_rows:
        baseline.setdefault(user, set()).add(country)

    created = 0

    for ev_id, user, country, ts in recent:
        # if user has no baseline -> treat first seen countries in last 24h as rare (optional: require >=1 baseline)
        seen = baseline.get(user, set())
        if country not in seen:
            title = f"{RID} for {user}"
            summary = (
                f"User '{user}' logged in from rare country '{country}' at {ts.isoformat()} "
                f"(baseline window: last 14d before 24h)."
            )

            det = Detection(
                rule_id=RID,
                kind="rule",
                severity=SEVERITY,
                title=title,
                summary=summary,
                status="open",
                assignee=None,
                tags=[RID, "rule", "geo"],
                event_ids=[ev_id],   # evidence = the rare success event
                features_json={"user": user, "country": country, "timestamp": ts.isoformat()},
            )
            db.add(det)
            created += 1

    if created:
        db.commit()
    return created