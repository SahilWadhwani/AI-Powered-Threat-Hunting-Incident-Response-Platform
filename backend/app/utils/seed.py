import argparse
from sqlalchemy.orm import Session
from ..core.db import SessionLocal
from ..models.user import User
from ..core.security import hash_password

def ensure_admin(db: Session, email: str, password: str) -> None:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"[seed] user already exists: {email} (role={existing.role})")
        return
    u = User(
        email=email,
        password_hash=hash_password(password),
        role="admin",
    )
    db.add(u)
    db.commit()
    print(f"[seed] created admin user: {email}")

def main():
    parser = argparse.ArgumentParser(description="Seed demo data")
    parser.add_argument("--email", required=True, help="admin email")
    parser.add_argument("--password", required=True, help="admin password (use a strong one!)")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        ensure_admin(db, args.email, args.password)
    finally:
        db.close()

if __name__ == "__main__":
    main()