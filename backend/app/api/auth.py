from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from ..schemas.auth import LoginIn, TokenPair
from ..core.deps import get_db
from ..core.jwt import create_access_token, create_refresh_token, decode_token
from ..services.users import get_user_by_email, create_user, check_user_credentials
from ..models.user import User
from ..core.security import hash_password  # ✅ use passlib wrapper

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: str  # "viewer", "analyst", or "admin"


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    # check if user exists
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    # ✅ use passlib CryptContext for hashing
    hashed = hash_password(req.password)

    user = User(email=req.email, password_hash=hashed, role=req.role)
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"id": user.id, "email": user.email, "role": user.role}


@router.post("/login", response_model=TokenPair)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = check_user_credentials(db, data.email, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    access = create_access_token(user.email, {"role": user.role})
    refresh = create_refresh_token(user.email)
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenPair)
def refresh(token: str):
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    if payload.get("typ") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token type"
        )
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    return TokenPair(
        access_token=create_access_token(sub),
        refresh_token=create_refresh_token(sub),
    )