from fastapi import APIRouter, Depends
from ..core.auth_deps import get_current_user
from ..schemas.auth import UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/me", response_model=UserOut)
def me(user = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "role": user.role}