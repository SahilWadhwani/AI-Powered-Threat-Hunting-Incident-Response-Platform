import json, time, random, requests
from datetime import datetime, timezone

URL = "http://127.0.0.1:8000/ingest/events"

def now():
    return datetime.now(timezone.utc).isoformat()

def batch():
    ip = f"203.0.113.{random.randint(1,254)}"
    return {
        "events": [
            {
                "timestamp": now(),
                "event_module": "auth",
                "event_action": "ssh_login_failed",
                "src_ip": ip,
                "user": "sahil",
                "fields": {"reason": "invalid_password"}
            },
            {
                "timestamp": now(),
                "event_module": "nginx",
                "event_action": "http_access",
                "src_ip": ip,
                "http_method": "GET",
                "http_path": random.choice(["/","/login","/admin","/wp-login.php"]),
                "user_agent": "synth/1.0"
            }
        ]
    }

if __name__ == "__main__":
    for _ in range(3):
        r = requests.post(URL, json=batch(), timeout=5)
        print(r.status_code, r.text)
        time.sleep(0.5)