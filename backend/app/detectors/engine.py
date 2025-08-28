from __future__ import annotations
from typing import Any, Dict, List, Tuple
from pathlib import Path
from datetime import datetime, timedelta, timezone
import yaml
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from ..models.event import EventNormalized
from ..models.detection import Detection

# ---- helpers ----

def parse_window(s: str) -> timedelta:
    # "5m", "10m", "1h", "24h"
    s = s.strip().lower()
    if s.endswith("m"):
        return timedelta(minutes=int(s[:-1]))
    if s.endswith("h"):
        return timedelta(hours=int(s[:-1]))
    raise ValueError(f"unsupported window '{s}' (use 'Xm' or 'Xh')")

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def _op_count_ge(count_expr: int, target: int) -> bool:
    return count_expr >= target

def _parse_threshold(th: Dict[str, str]) -> Tuple[str, int]:
    # e.g., {"count": ">= 6"} → ("count", 6)
    expr = th.get("count")
    if not expr or not expr.startswith(">="):
        raise ValueError("only 'count: \">= N\"' supported for MVP")
    n = int(expr.split(">=")[1].strip())
    return ("count", n)

def _build_filters(where: Dict[str, Any]) -> List[Any]:
    """
    where:
      all:
        - event_module: "auth"
        - event_action: "ssh_login_failed"
    """
    conds: List[Any] = []
    if not where:
        return conds
    if "all" in where:
        for item in where["all"]:
            # single-key dicts
            if not isinstance(item, dict) or len(item) != 1:
                continue
            k, v = next(iter(item.items()))
            if k == "event_module":
                conds.append(EventNormalized.event_module == str(v))
            elif k == "event_action":
                conds.append(EventNormalized.event_action == str(v))
            elif k == "user":
                conds.append(EventNormalized.user == str(v))
            elif k == "src_ip":
                conds.append(EventNormalized.src_ip == str(v))
            elif k == "http_path":
                conds.append(EventNormalized.http_path == str(v))
            else:
                # ignore unknown keys in MVP
                pass
    return conds

# ---- rule loader & runner ----

def load_rules(rules_dir: Path) -> List[Dict[str, Any]]:
    rules: List[Dict[str, Any]] = []
    for f in sorted(rules_dir.glob("*.yml")):
        with f.open("r", encoding="utf-8") as fh:
            rules.append(yaml.safe_load(fh))
    return rules

def run_rule(db: Session, rule: Dict[str, Any]) -> int:
    """
    Returns number of detections created.
    """
    rid = rule.get("id") or "unnamed"
    severity = (rule.get("severity") or "medium").lower()
    where = rule.get("where") or {}
    group_by = rule.get("group_by") or []
    window = parse_window(rule.get("window", "5m"))
    th_key, th_value = _parse_threshold(rule.get("threshold", {"count": ">= 10"}))

    end = now_utc()
    start = end - window

    # build base query in window
    conds = [EventNormalized.timestamp >= start, EventNormalized.timestamp < end]
    conds += _build_filters(where)

    # group_by supported: ["src_ip", "user"]
    group_cols = []
    for g in group_by:
        if g == "src_ip":
            group_cols.append(EventNormalized.src_ip)
        elif g == "user":
            group_cols.append(EventNormalized.user)
        else:
            # skip unsupported in MVP
            pass

    stmt = select(
        *(group_cols if group_cols else []),
        func.count().label("cnt")
    ).where(and_(*conds)).group_by(*group_cols) if group_cols else select(
        func.count().label("cnt")
    ).where(and_(*conds))

    rows = db.execute(stmt).all()
    created = 0

    for row in rows:
        if group_cols:
            # row like: (<group values...>, cnt)
            *groups, cnt = row
        else:
            (cnt,) = row

        if cnt is None:
            continue

        if th_key == "count" and _op_count_ge(cnt, th_value):
            # fetch example event ids for evidence (last 50)
            sel_ids = select(EventNormalized.id).where(and_(*conds))
            if group_cols:
                for gi, gcol in enumerate(group_cols):
                    sel_ids = sel_ids.where(gcol == groups[gi])
            sel_ids = sel_ids.order_by(EventNormalized.id.desc()).limit(50)
            ev_ids = [r[0] for r in db.execute(sel_ids).all()]

            title = f"{rid} hit"
            summary = f"Rule {rid} matched with count={cnt} in window={window}; group={groups if group_cols else 'all'}"

            det = Detection(
                rule_id=rid,
                kind="rule",
                severity=severity,
                title=title,
                summary=summary,
                event_ids=ev_ids,
                features_json=None,
                status="open",
                assignee=None,
                tags=[rid, "rule"],
            )
            db.add(det)
            created += 1

    if created:
        db.commit()
    return created

def run_all_rules(db: Session, rules_dir: Path) -> Dict[str, int]:
    results: Dict[str, int] = {}
    for rule in load_rules(rules_dir):
        rid = rule.get("id", "unnamed")
        try:
            c = run_rule(db, rule)
            results[rid] = c
        except Exception as e:
            results[rid] = -1  # indicate failure
    return results