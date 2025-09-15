# from fastapi import APIRouter, Depends
# from sqlalchemy.orm import Session
# from datetime import datetime, timezone, timedelta
# import random
# import logging
# from pathlib import Path
# from typing import Any, Dict

# from ..core.deps import get_db
# from ..core.auth_deps import get_current_user
# from ..models.event import EventNormalized
# from ..detectors.engine import run_all_rules

# router = APIRouter(prefix="/demo", tags=["demo"])

# RULES_DIR = Path(__file__).resolve().parents[1] / "detectors" / "rules"
# log = logging.getLogger(__name__)

# def _utcnow():
#     return datetime.now(timezone.utc)

# def _rand_ip():
#     return ".".join(str(random.randint(10, 250)) for _ in range(4))

# @router.post("/generate")
# def generate_demo(db: Session = Depends(get_db), user=Depends(get_current_user)) -> Dict[str, Any]:
#     try:
#         now = _utcnow()
#         src_ip = _rand_ip()
#         u = user.email.split("@")[0]

#         FAIL_COUNT = 10
#         WINDOW_MIN = 5

#         # 1) Burst of failed auth logins (trip SSH-Bruteforce rule)
#         for _ in range(FAIL_COUNT):
#             db.add(EventNormalized(
#                 timestamp=now - timedelta(minutes=random.randint(0, WINDOW_MIN)),
#                 event_module="auth",
#                 event_action="ssh_login_failed",
#                 src_ip=src_ip,
#                 user=u,
#                 http_path=None,
#                 country=None,
#             ))

#         # 2) A few benign web requests
#         for path in ["/", "/status", "/login", "/api/health"]:
#             db.add(EventNormalized(
#                 timestamp=now - timedelta(minutes=random.randint(0, 60)),
#                 event_module="nginx",
#                 event_action="http_request",
#                 src_ip=_rand_ip(),
#                 user=None,
#                 http_path=path,
#                 country=random.choice([None, "US", "DE", "IN"]),
#             ))

#         db.commit()

#         # 3) Web-scan burst (one IP, many distinct paths in a short window)
#         scan_ip = _rand_ip()
#         ATTACK_PATHS = [
#             "/wp-login.php", "/phpmyadmin", "/admin", "/.git/config",
#             "/.env", "/server-status", "/xmlrpc.php", "/index.php",
#             "/login", "/admin/login", "/vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php",
#         ]
#         for p in ATTACK_PATHS:
#             db.add(EventNormalized(
#                 timestamp=now - timedelta(minutes=random.randint(0, 5)),
#                 event_module="nginx",
#                 event_action="http_request",
#                 src_ip=scan_ip,
#                 user=None,
#                 http_path=p,
#                 country=random.choice(["US", "CN", "RU", "DE", "IN", None]),
#             ))

#         # 4) Multi-user brute force (same IP targets many usernames)
#         mu_ip = _rand_ip()
#         USERNAMES = ["admin", "alice", "bob", "ec2-user", "ubuntu", "git", "postgres"]
#         for uname in USERNAMES[:5]:  # 5 distinct users to exceed threshold
#             db.add(EventNormalized(
#                 timestamp=now - timedelta(minutes=random.randint(0, 5)),
#                 event_module="auth",
#                 event_action="ssh_login_failed",
#                 src_ip=mu_ip,
#                 user=uname,
#                 http_path=None,
#                 country=None,
#             ))
#         # a few more from same IP to those users
#         for _ in range(3):
#             db.add(EventNormalized(
#                 timestamp=now - timedelta(minutes=random.randint(0, 5)),
#                 event_module="auth",
#                 event_action="ssh_login_failed",
#                 src_ip=mu_ip,
#                 user=random.choice(USERNAMES[:5]),
#                 http_path=None,
#                 country=None,
#             ))

#         db.commit()


#                 # --- Geo rare login demo ---
#         # Historical successes (user 'geo_user') from US
#         geo_user = "geo_user"
#         for days_ago in [3, 7, 10]:
#             db.add(EventNormalized(
#                 timestamp=now - timedelta(days=days_ago),
#                 event_module="auth",
#                 event_action="ssh_login_success",
#                 src_ip=_rand_ip(),
#                 user=geo_user,
#                 http_path=None,
#                 country="US",
#             ))

#         # New success from a rare country (CN) within the current window
#         db.add(EventNormalized(
#             timestamp=now - timedelta(minutes=random.randint(0, 5)),
#             event_module="auth",
#             event_action="ssh_login_success",
#             src_ip=_rand_ip(),
#             user=geo_user,
#             http_path=None,
#             country="CN",
#         ))

#         # 5) Run all rules
#         results = run_all_rules(db, RULES_DIR)

#         return {
#             "ok": True,
#             "generated": {
#                 "auth_failed": FAIL_COUNT,
#                 "web": 4,
#                 "web_scan_paths": len(ATTACK_PATHS),
#                 "ssh_multiuser": 8,
#                 "geo_rare_login": 1,
#             },
#             "rules": results,
#             "source_ip": src_ip,
#             "scan_ip": scan_ip,
#             "multiuser_ip": mu_ip,
#             "geo_user": geo_user,
#         }

#     except Exception as e:
#         log.exception("demo.generate failed")
#         return {"ok": False, "error": str(e)}



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

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

def _rand_ip() -> str:
    return ".".join(str(random.randint(10, 250)) for _ in range(4))

@router.post("/generate")
def generate_demo(db: Session = Depends(get_db), user=Depends(get_current_user)) -> Dict[str, Any]:
    try:
        now = _utcnow()
        src_ip = _rand_ip()
        u = (user.email.split("@")[0]).replace("@", "_")

        FAIL_COUNT = 10
        WINDOW_MIN = 5

        # 1) Burst of failed auth logins (trip SSH brute-force YAML rule)
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

        # 3) Web-scan burst (one IP, many distinct paths in short window) — trips Web-Scan YAML rule
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

        # 4) Multi-user SSH brute-force (same IP hits many users) — trips SSH-MultiUser-Bruteforce
        multi_ip = _rand_ip()
        multi_users = ["admin", "ubuntu", "ec2-user", "bob", "alice"]
        for who in multi_users + multi_users[:3]:
            db.add(EventNormalized(
                timestamp=now - timedelta(minutes=random.randint(0, 5)),
                event_module="auth",
                event_action="ssh_login_failed",
                src_ip=multi_ip,
                user=who,
                http_path=None,
                country=None,
            ))

        # --- GEO RARE LOGIN deterministically ---
        # Use a unique username each run to avoid old history clashes
        geo_user = f"geo_user_{int(now.timestamp())}"

        # History (last 30d, *before* the current window): user logged in from US only
        for days_ago in (7, 3, 1):  # all outside the current 10m window
            db.add(EventNormalized(
                timestamp=now - timedelta(days=days_ago, minutes=30),
                event_module="auth",
                event_action="ssh_login_success",
                src_ip=_rand_ip(),
                user=geo_user,
                http_path=None,
                country="US",
            ))

        # Current-window success from a *new* country 'CN' -> should fire
        db.add(EventNormalized(
            timestamp=now - timedelta(minutes=1),
            event_module="auth",
            event_action="ssh_login_success",
            src_ip=_rand_ip(),
            user=geo_user,
            http_path=None,
            country="CN",
        ))
        # --- end GEO RARE LOGIN block ---

        db.commit()


        # 5) --- 5xx spike demo (possible outage) ---
        for _ in range(25):
            db.add(EventNormalized(
                timestamp=now - timedelta(minutes=random.randint(0, 5)),
                event_module="nginx",
                event_action="http_5xx",   # <-- matches YAML rule
                src_ip=_rand_ip(),
                user=None,
                http_path=None,
                country=None,
            ))
        # --- end 5xx spike demo ---

        # 5) Run rules
        results = run_all_rules(db, RULES_DIR)

        return {
            "ok": True,
            "generated": {
                "auth_failed": FAIL_COUNT,
                "web": 4,
                "web_scan_paths": len(ATTACK_PATHS),
                "ssh_multiuser": len(multi_users) + 3,
                "geo_rare_login": 1,
                "http_5xx": 25,
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