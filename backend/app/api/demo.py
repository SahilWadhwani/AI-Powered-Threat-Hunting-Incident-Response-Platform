from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
import random
import logging
from pathlib import Path
from typing import Any, Dict

from ..core.deps import get_db
from ..core.auth_deps import get_current_user
from ..models.event import EventNormalized
from ..detectors.engine import run_all_rules

router = APIRouter(prefix="/demo", tags=["demo"])

RULES_DIR = Path(__file__).resolve().parents[1] / "detectors" / "rules"
log = logging.getLogger(__name__)

def _utcnow():
    return datetime.now(timezone.utc)

def _rand_ip():
    return ".".join(str(random.randint(10, 250)) for _ in range(4))

@router.post("/generate")
def generate_demo(db: Session = Depends(get_db), user=Depends(get_current_user)) -> Dict[str, Any]:
    try:
        now = _utcnow()
        src_ip = _rand_ip()
        u = user.email.split("@")[0]

        FAIL_COUNT = 10
        WINDOW_MIN = 5

        # 1) Burst of failed auth logins (trip brute-force rule)
        for _ in range(FAIL_COUNT):
            db.add(EventNormalized(
                timestamp=now - timedelta(minutes=random.randint(0, WINDOW_MIN)),
                event_module="auth",
                event_action="ssh_login_failed",
                src_ip=src_ip,
                user=u,
                http_path=None,
                country=None,
            ))

        # 2) A few benign web requests
        for path in ["/", "/status", "/login", "/api/health"]:
            db.add(EventNormalized(
                timestamp=now - timedelta(minutes=random.randint(0, 60)),
                event_module="nginx",
                event_action="http_request",
                src_ip=_rand_ip(),
                user=None,
                http_path=path,
                country=random.choice([None, "US", "DE", "IN"]),
            ))

        db.commit()

        # 3) Web-scan burst (one IP, many distinct paths in a short window)
        scan_ip = _rand_ip()
        ATTACK_PATHS = [
            "/wp-login.php", "/phpmyadmin", "/admin", "/.git/config",
            "/.env", "/server-status", "/xmlrpc.php", "/index.php",
            "/login", "/admin/login", "/vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php",
        ]
        for p in ATTACK_PATHS:
            db.add(EventNormalized(
                timestamp=now - timedelta(minutes=random.randint(0, 5)),
                event_module="nginx",
                event_action="http_request",
                src_ip=scan_ip,
                user=None,
                http_path=p,
                country=random.choice(["US", "CN", "RU", "DE", "IN", None]),
            ))

        # 4) Multi-user brute-force from one IP
        multi_ip = _rand_ip()
        for uname in ["admin", "alice", "bob", "ec2-user", "ubuntu", "root", "test", "guest"]:
            db.add(EventNormalized(
                timestamp=now - timedelta(minutes=random.randint(0, 5)),
                event_module="auth",
                event_action="ssh_login_failed",
                src_ip=multi_ip,
                user=uname,
                http_path=None,
                country=None,
            ))

        # 5) Suspicious geo login (success from rare country)
        geo_user = f"geo_user_{int(now.timestamp())}"
        db.add(EventNormalized(
            timestamp=now,
            event_module="auth",
            event_action="ssh_login_success",
            src_ip=_rand_ip(),
            user=geo_user,
            http_path=None,
            country="CN",   # unusual location
        ))

        # 6) HTTP 5xx spike (simulate outage traffic)
        spike_ip = _rand_ip()
        for _ in range(25):
            db.add(EventNormalized(
                timestamp=now - timedelta(seconds=random.randint(0, 60)),
                event_module="nginx",
                event_action="http_request",
                src_ip=spike_ip,
                user=None,
                http_path="/api/resource",
                country="US",
                fields_json={"status": 500},
            ))

        # 7) Inject anomalies for ML detector (weird combos)
        for _ in range(5):
            db.add(EventNormalized(
                timestamp=now,
                event_module="nginx",
                event_action="http_request",
                src_ip=f"203.{random.randint(100,200)}.{random.randint(0,255)}.{random.randint(0,255)}",
                user="strange_user_" + str(random.randint(1000, 9999)),
                http_path="/weird/path/" + str(random.randint(1000, 9999)),
                country="ZZ",   # uncommon country code
            ))

        db.commit()

        # Run rules (YAML + Python + ML)
        results = run_all_rules(db, RULES_DIR)

        return {
            "ok": True,
            "generated": {
                "auth_failed": FAIL_COUNT,
                "web": 4,
                "web_scan_paths": len(ATTACK_PATHS),
                "ssh_multiuser": 8,
                "geo_rare_login": 1,
                "http_5xx": 25,
                "ml_anomalies": 5,
            },
            "rules": results,
            "source_ip": src_ip,
            "scan_ip": scan_ip,
            "multiuser_ip": multi_ip,
            "geo_user": geo_user,
        }

    except Exception as e:
        log.exception("demo.generate failed")
        return {"ok": False, "error": str(e)}