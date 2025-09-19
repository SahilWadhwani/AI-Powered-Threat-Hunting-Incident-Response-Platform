from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import numpy as np
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from sklearn.ensemble import IsolationForest

from backend.app.models.event import EventNormalized

NAME = "Anomaly-Login-Combo"

# Parameters
WINDOW_HOURS = 24      # look at events in last 24h
MAX_EVENTS = 5000      # cap rows for performance
TOP_N = 5              # report top-N anomalies

def _utcnow():
    return datetime.now(timezone.utc)

def _encode_str(s: str | None) -> int:
    if not s:
        return 0
    # stable hash -> int in a fixed range
    return abs(hash(s)) % 10000

def run(db: Session, since: datetime | None = None, until: datetime | None = None) -> List[Dict[str, Any]]:
    if not until:
        until = _utcnow()
    if not since:
        since = until - timedelta(hours=WINDOW_HOURS)

    ev = EventNormalized

    # fetch events
    stmt = (
        select(ev.id, ev.src_ip, ev.user, ev.http_path)
        .where(and_(ev.timestamp >= since, ev.timestamp <= until))
        .order_by(ev.id.desc())
        .limit(MAX_EVENTS)
    )
    rows = db.execute(stmt).all()
    if not rows:
        return []

    # encode categorical into numeric
    X = []
    ids = []
    for eid, ip, user, path in rows:
        ids.append(eid)
        X.append([
            _encode_str(ip),
            _encode_str(user),
            _encode_str(path),
        ])
    X = np.array(X)

    # train isolation forest
    clf = IsolationForest(n_estimators=50, contamination=0.01, random_state=42)
    scores = clf.fit_predict(X)  # -1 = anomaly, 1 = normal
    decision = clf.decision_function(X)  # the raw scores (lower = more anomalous)

    # collect anomalies
    anomalies = []
    for eid, label, score in zip(ids, scores, decision):
        if label == -1:  # anomaly
            anomalies.append((eid, score))

    # sort by score ascending (most anomalous first)
    anomalies.sort(key=lambda x: x[1])
    anomalies = anomalies[:TOP_N]

    findings: List[Dict[str, Any]] = []
    for eid, score in anomalies:
        findings.append({
            "rule_name": NAME,
            "title": f"Anomalous event #{eid}",
            "severity": "medium",
            "summary": f"IsolationForest flagged event {eid} as anomalous (score={score:.3f}).",
            "evidence_event_ids": [eid],
            "features": {"score": float(score)},
        })

    return findings