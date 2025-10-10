#  SentinelX : AI-Powered Threat Hunting & Incident Response Platform

**SentinelX** is a full-stack, modular security operations platform built to demonstrate real-world **Threat Detection**, **Incident Response**, and **RBAC-based Access Control** workflows.  
It combines a modern **Next.js frontend** with a **FastAPI backend**, following production-grade security practices.

---

##  Features

###  Authentication & RBAC
- JWT-based secure authentication (Access + Refresh tokens)
- Role-based access control (RBAC)
  - **Admin** → Full access (can block/unblock IPs)
  - **Analyst** → Can manage detections and respond
  - **Viewer** → Read-only dashboard
- Protected routes both on **backend** (`require_roles()`) and **frontend** (`RoleGate` component)

###  Backend (FastAPI)
- Modular API under `/backend/app/api`
- Endpoints:
  - `/auth/register` - Register users with roles
  - `/auth/login` - Login and issue JWTs
  - `/auth/refresh` - Refresh access tokens
  - `/respond/block_ip` - Block suspicious IPs
  - `/respond/blocks` - List current block rules
  - `/respond/blocks/{id}/unblock` - Unblock IPs
- SQLAlchemy ORM + Alembic migrations
- Passlib password hashing (Argon2id)
- CORS configured for frontend (localhost:3000)

###  Frontend (Next.js + TypeScript)
- Built using **Next.js 14 App Router**
- State management via **React Query** and global **auth store**
- Secure route protection with RoleGate
- Pages:
  - `/dashboard` - Overview of detections & metrics
  - `/detections` - Active rules and alerts
  - `/events` - Event timeline
  - `/respond` - Blocklist & Unblock actions (restricted to Analysts/Admins)

###  Database (PostgreSQL)
- Tables:
  - `users` - Authentication + Role storage
  - `block_rules` - IP block tracking
  - `detections`, `events`, `metrics` (expandable modules)
- SQLAlchemy models and services layer for clean separation

---

##  Working

###

<img width="2048" height="860" alt="image" src="https://github.com/user-attachments/assets/5a8315cd-b41b-4a31-b77a-c7f4b0333416" />
<img width="2048" height="911" alt="image" src="https://github.com/user-attachments/assets/225c2d03-38ee-49b0-a734-1aad0a40d74d" />
<img width="1705" height="769" alt="image" src="https://github.com/user-attachments/assets/80aff03a-eacd-4493-81a3-bc5a77f5aadd" />
<img width="2048" height="1173" alt="image" src="https://github.com/user-attachments/assets/6ac60b0b-5790-4812-9081-f4466d72ba66" />



##  Folder Structure

```

sentinelx/
│
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes
│   │   ├── core/             # Config, JWT, security
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── services/         # Business logic
│   │   └── main.py           # App entrypoint
│   └── requirements.txt
│
├── frontend/
│   ├── src/app/              # Next.js pages (App Router)
│   ├── src/components/       # Reusable UI components
│   ├── src/lib/              # API utilities (fetch, respond, etc.)
│   ├── src/store/            # Auth store
│   └── package.json
│
└── README.md

````

---

##  Testing RBAC Locally

Seed test users:
```bash
python - <<'PY'
import sqlalchemy as sa
from datetime import datetime, timezone
from backend.app.core.config import settings
from backend.app.core.security import hash_password

e = sa.create_engine(settings.database_url)
now = datetime.now(timezone.utc)

def seed(email, password, role):
    hashed = hash_password(password)
    with e.begin() as conn:
        conn.execute(sa.text("DELETE FROM users WHERE email=:email"), {"email": email})
        conn.execute(sa.text("""
            INSERT INTO users (email, password_hash, role, created_at)
            VALUES (:email, :pw, :role, :created_at)
        """), {"email": email, "pw": hashed, "role": role, "created_at": now})
    print(f" {email} ({role}) seeded")

seed("admin@local.com", "Admin123!", "admin")
seed("analyst@local.com", "Analyst123!", "analyst")
seed("viewer@local.com", "Viewer123!", "viewer")
PY
````

Login to test:

```bash
curl -s http://127.0.0.1:8000/auth/login \
  -H 'content-type: application/json' \
  -d '{"email":"admin@local.com","password":"Admin123!"}' | jq .
```

---

##  Tech Stack

| Layer             | Technology                                       |
| ----------------- | ------------------------------------------------ |
| **Frontend**      | Next.js 14, React Query, TailwindCSS, TypeScript |
| **Backend**       | FastAPI, SQLAlchemy, Passlib (Argon2id), JWT     |
| **Database**      | PostgreSQL                                       |
| **Auth**          | Role-based (viewer / analyst / admin)            |
| **UI Components** | ShadCN + Lucide Icons                            |
| **Dev Tools**     | Docker (planned), Uvicorn, Alembic               |

---

##  Upcoming Add-Ons

*  **Audit Logging** — Track user actions (e.g., who blocked/unblocked)
*  **Dockerization** — One-command startup using `docker-compose`
*  **SIEM-like Analytics** — Threat feed visualization
*  **CVE Feed Integration** — Real-time vulnerability intelligence
*  **SOC Dashboard Mode** — Multi-user event correlation

---

##  How to Run

###  Backend

```bash
cd backend
uvicorn backend.api.main:app --reload --port 8000
```

###  Frontend

```bash
cd frontend
npm install
npm run dev
```

Then visit:
 [http://localhost:3000/dashboard](http://localhost:3000/dashboard)

---

##  Author

**Sahil Wadhwani**
MS Computer Science @ USC | Security Engineer & Full-Stack Developer
 [Portfolio](https://www.sahilw.dev) • [LinkedIn](https://www.linkedin.com/in/sahil-wadhwani-06848122a/) • [GitHub](https://github.com/SahilWadhwani)

---