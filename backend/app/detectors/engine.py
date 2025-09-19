from __future__ import annotations

from typing import Any, Dict, List, Tuple, Callable
from pathlib import Path
from datetime import datetime, timedelta, timezone
import importlib.util
import logging
import sys
import re

import yaml
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from ..models.event import EventNormalized
from ..models.detection import Detection


log = logging.getLogger(__name__)

# ---------------- helpers ----------------

def parse_window(s: str) -> timedelta:
    """
    Accepts '5m' or '1h' (minutes / hours).
    """
    s = (s or "").strip().lower()
    if s.endswith("m"):
        return timedelta(minutes=int(s[:-1]))
    if s.endswith("h"):
        return timedelta(hours=int(s[:-1]))
    raise ValueError(f"unsupported window '{s}' (use 'Xm' or 'Xh')")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _op_count_ge(count_expr: int, target: int) -> bool:
    return int(count_expr) >= int(target)


def _parse_threshold(th: Dict[str, Any]) -> Tuple[str, int, str | None]:
    """
    Parse:
      threshold:
        count: ">= 6"
        distinct_field: http_path   # optional
    """
    expr = (th or {}).get("count")
    if not isinstance(expr, str):
        raise ValueError("threshold.count must be a string like '>= 6'")

    # tolerate spaces: ">=6", ">= 6", "  >=   6  "
    m = re.match(r"^\s*>=\s*(\d+)\s*$", expr)
    if not m:
        raise ValueError("only 'count: \">= N\"' supported for MVP")

    n = int(m.group(1))
    distinct_field = (th or {}).get("distinct_field")
    if distinct_field is not None and not isinstance(distinct_field, str):
        raise ValueError("threshold.distinct_field must be a string when present")

    return ("count", n, distinct_field)


def _build_filters(where: Dict[str, Any]) -> List[Any]:
    """
    where:
      all:
        - event_module: "auth"
        - event_action: "ssh_login_failed"
        - user: "alice"
        - src_ip: "1.2.3.4"
        - http_path: "/login"
        - country: "US"
    """
    conds: List[Any] = []
    if not where:
        return conds

    if "all" in where:
        for item in where["all"]:
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
            elif k == "country":
                conds.append(EventNormalized.country == str(v))
            # ignore unknown keys
    return conds


# ---------------- rule loaders ----------------

def load_yaml_rules(rules_dir: Path) -> List[Dict[str, Any]]:
    rules: List[Dict[str, Any]] = []
    for f in sorted(rules_dir.glob("*.yml")):
        try:
            with f.open("r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
                if isinstance(data, dict):
                    rules.append(data)
        except Exception:
            log.exception("failed to load YAML rule: %s", f)
    return rules


import traceback, logging
log = logging.getLogger(__name__)
def load_py_rules(rules_dir: Path) -> List[Dict[str, Any]]:
    py_rules: List[Dict[str, Any]] = []
    for f in sorted(rules_dir.glob("*.py")):
        if f.name.startswith("_"):
            continue
        spec = importlib.util.spec_from_file_location(f"detector_{f.stem}", f)
        if not spec or not spec.loader:
            continue
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)  # type: ignore
        except Exception:
            log.error("Failed to import rule %s\n%s", f.name, traceback.format_exc())
            continue
        name = getattr(mod, "NAME", None)
        run_fn = getattr(mod, "run", None)
        if isinstance(name, str) and callable(run_fn):
            py_rules.append({"id": name, "callable": run_fn})
    return py_rules


# ---------------- YAML rule runner ----------------

def run_yaml_rule(db: Session, rule: Dict[str, Any]) -> int:
    rid = rule.get("id") or "unnamed"
    severity = (rule.get("severity") or "medium").lower()
    where = rule.get("where") or {}
    group_by = rule.get("group_by") or []
    window = parse_window(rule.get("window", "5m"))
    th_key, th_value, distinct_field = _parse_threshold(rule.get("threshold", {"count": ">= 10"}))

    end = now_utc()
    start = end - window

    conds = [EventNormalized.timestamp >= start, EventNormalized.timestamp < end]
    conds += _build_filters(where)

    group_cols = []
    for g in group_by:
        if g == "src_ip":
            group_cols.append(EventNormalized.src_ip)
        elif g == "user":
            group_cols.append(EventNormalized.user)
        elif g == "country":
            group_cols.append(EventNormalized.country)
        elif g == "http_path":
            group_cols.append(EventNormalized.http_path)

    # distinct count support
    if distinct_field:
        target_col = getattr(EventNormalized, distinct_field, None)
        count_expr = func.count(func.distinct(target_col)) if target_col is not None else func.count()
    else:
        count_expr = func.count()

    if group_cols:
        stmt = (
            select(*group_cols, count_expr.label("cnt"))
            .where(and_(*conds))
            .group_by(*group_cols)
        )
    else:
        stmt = select(count_expr.label("cnt")).where(and_(*conds))

    rows = db.execute(stmt).all()
    created = 0

    for row in rows:
        if group_cols:
            *groups, cnt = row
        else:
            (cnt,) = row

        if cnt is None:
            continue

        if th_key == "count" and _op_count_ge(cnt, th_value):
            # Collect evidence event IDs (latest first, cap to 50)
            sel_ids = select(EventNormalized.id).where(and_(*conds))
            if group_cols:
                for gi, gcol in enumerate(group_cols):
                    sel_ids = sel_ids.where(gcol == groups[gi])
            sel_ids = sel_ids.order_by(EventNormalized.id.desc()).limit(50)
            ev_ids = [r[0] for r in db.execute(sel_ids).all()]

            window_str = str(window)
            group_repr = f"{groups if group_cols else 'all'}"
            distinct_tag = f" (distinct={distinct_field})" if distinct_field else ""

            title = f"{rid} hit"
            summary = (
                f"Rule {rid} matched with count={int(cnt)}{distinct_tag} "
                f"in window={window_str}; group={group_repr}"
            )

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


# ---------------- Python rule runner ----------------

def persist_python_findings(db: Session, rid: str, findings: List[Dict[str, Any]]) -> int:
    created = 0
    for f in findings or []:
        ev_ids = list(map(int, f.get("evidence_event_ids", [])))
        severity = (f.get("severity") or "medium").lower()
        title = f.get("title") or f"{rid} hit"
        summary = f.get("summary") or f"Rule {rid} fired"
        det = Detection(
            rule_id=rid,
            kind="rule",
            severity=severity,
            title=title,
            summary=summary,
            event_ids=ev_ids,
            features_json=f.get("features") or None,
            status="open",
            assignee=None,
            tags=[rid, "rule"],
        )
        db.add(det)
        created += 1
    if created:
        db.commit()
    return created


# ---------------- entrypoint ----------------

def run_all_rules(db: Session, rules_dir: Path) -> Dict[str, int]:
    results: Dict[str, int] = {}

    # YAML rules
    for rule in load_yaml_rules(rules_dir):
        rid = rule.get("id", "unnamed")
        try:
            c = run_yaml_rule(db, rule)
            results[rid] = c
        except Exception:
            log.exception("failed running YAML rule '%s'", rid)
            results[rid] = -1

    # Python rules
    for pr in load_py_rules(rules_dir):
        rid = pr["id"]
        run_fn: Callable[[Session, datetime | None, datetime | None], List[Dict[str, Any]]] = pr["callable"]
        try:
            end = now_utc()
            start = end - timedelta(minutes=10)  # default timebox (rule may ignore)
            findings = run_fn(db, since=start, until=end)
            c = persist_python_findings(db, rid, findings)
            results[rid] = results.get(rid, 0) + c
        except Exception:
            log.exception("failed running Python rule '%s'", rid)
            results[rid] = -1

    # ML rules (detectors/ml/*.py)
    ml_dir = rules_dir.parent / "ml"
    for pr in load_py_rules(ml_dir):
        rid = pr["id"]
        run_fn = pr["callable"]
        try:
            end = now_utc()
            start = end - timedelta(hours=24)
            findings = run_fn(db, since=start, until=end)
            c = persist_python_findings(db, rid, findings)
            results[rid] = results.get(rid, 0) + c
        except Exception:
            results[rid] = -1

    return results