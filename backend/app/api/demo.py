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

        # 3) Run rules
        results = run_all_rules(db, RULES_DIR)

        return {
            "ok": True,
            "generated": {"auth_failed": 7, "web": 4},
            "rules": results,
            "source_ip": src_ip,
        }

    except Exception as e:
        log.exception("demo.generate failed")
        return {"ok": False, "error": str(e)}