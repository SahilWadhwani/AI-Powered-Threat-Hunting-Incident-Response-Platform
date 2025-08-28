from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from jose import jwt, JWTError
from .config import settings

# Token lifetimes (tweak later as needed)
ACCESS_MINUTES = 15
REFRESH_DAYS = 7
ALGO = "HS256"

def _expiry(minutes: int = 0, days: int = 0) -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=minutes, days=days)

def create_access_token(sub: str, extra: Optional[dict]=None) -> str:
    to_encode: dict[str, Any] = {"sub": sub, "exp": _expiry(minutes=ACCESS_MINUTES), "typ": "access"}
    if extra:
        to_encode.update(extra)
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=ALGO)

def create_refresh_token(sub: str) -> str:
    to_encode: dict[str, Any] = {"sub": sub, "exp": _expiry(days=REFRESH_DAYS), "typ": "refresh"}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=ALGO)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[ALGO])
    except JWTError as e:
        raise ValueError("invalid token") from e