from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.security import create_access_token, verify_password
from app.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = user_service.get_by_email(db, body.email)
    if not user or not verify_password(body.password, user.hashed_password):
        raise UnauthorizedError("Incorrect email or password")
    if not user.is_active:
        raise UnauthorizedError("Account is inactive")
    token = create_access_token(user.id, extra_claims={"role": user.role.value})
    return TokenResponse(access_token=token)
