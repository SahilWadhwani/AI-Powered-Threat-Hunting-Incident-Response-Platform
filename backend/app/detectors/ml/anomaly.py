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
    """
    Detect anomalous login combinations using IsolationForest +
    model-based explainability (feature deviation importance).
    """
    if not until:
        until = _utcnow()
    if not since:
        since = until - timedelta(hours=WINDOW_HOURS)

    ev = EventNormalized

    #  Fetch recent events
    stmt = (
        select(ev.id, ev.src_ip, ev.user, ev.http_path)
        .where(and_(ev.timestamp >= since, ev.timestamp <= until))
        .order_by(ev.id.desc())
        .limit(MAX_EVENTS)
    )
    rows = db.execute(stmt).all()
    if not rows:
        return []

    #  Encode categorical features -> numeric for model
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

    #  Train IsolationForest
    clf = IsolationForest(n_estimators=50, contamination=0.01, random_state=42)
    preds = clf.fit_predict(X)        # -1 = anomaly, 1 = normal
    scores = clf.decision_function(X) # Lower = more anomalous

    #  Compute global mean of all (approx normal baseline)
    mean_vec = np.mean(X[preds == 1], axis=0) if np.any(preds == 1) else np.mean(X, axis=0)

    #  Compute per-feature deviations for anomalies
    anomalies = []
    for i, (eid, pred, score) in enumerate(zip(ids, preds, scores)):
        if pred != -1:
            continue

        feature_vec = X[i]
        deviations = np.abs(feature_vec - mean_vec)
        total_dev = np.sum(deviations) or 1.0
        importance = deviations / total_dev

        importance_dict = {
            "src_ip": round(float(importance[0]), 3),
            "user": round(float(importance[1]), 3),
            "http_path": round(float(importance[2]), 3),
        }

        # Find top contributing feature
        top_feature = max(importance_dict, key=importance_dict.get)
        explanation = (
            f"Model detected anomalous {top_feature} pattern "
            f"based on deviation from typical behavior in last {WINDOW_HOURS}h."
        )

        anomalies.append((eid, score, top_feature, importance_dict, explanation))

    #  Sort anomalies (most anomalous first)
    anomalies.sort(key=lambda x: x[1])
    anomalies = anomalies[:TOP_N]

    # Format findings for DB or API
    findings: List[Dict[str, Any]] = []
    for eid, score, top, importance, explanation in anomalies:
        findings.append({
            "rule_name": NAME,
            "title": f"Anomalous event #{eid}",
            "severity": "medium",
            "summary": f"IsolationForest flagged event {eid} as anomalous (score={score:.3f}).",
            "evidence_event_ids": [eid],
            "features": {
                "score": float(score),
                "top_contributor": top,
                "importance": importance,
                "explanation": explanation
            },
        })

    return findings