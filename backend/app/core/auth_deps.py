from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from .jwt import decode_token
from .deps import get_db
from ..services.users import get_user_by_email

bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(db: Session = Depends(get_db),
                     creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)):
    if creds is None or not creds.scheme.lower() == "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid authorization")

    try:
        payload = decode_token(creds.credentials)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if payload.get("typ") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token type")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    user = get_user_by_email(db, sub)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user

def require_roles(*allowed_roles: str):
    def dep(user = Depends(get_current_user)):
        role = (getattr(user, "role", None) or "").lower()
        if role not in {r.lower() for r in allowed_roles}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="insufficient role")
        return user
    return dep