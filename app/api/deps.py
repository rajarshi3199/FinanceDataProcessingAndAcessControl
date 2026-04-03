from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_token_safe
from app.database import get_db
from app.models.user import User, UserRole
from app.services import user_service

security = HTTPBearer(auto_error=False)


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> User:
    if creds is None or not creds.credentials:
        raise UnauthorizedError("Missing bearer token")
    payload = decode_token_safe(creds.credentials)
    if not payload or "sub" not in payload:
        raise UnauthorizedError("Invalid token")
    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise UnauthorizedError("Invalid token subject")
    user = user_service.get_by_id(db, user_id)
    if not user:
        raise UnauthorizedError("User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
    return user


def require_roles(*allowed: UserRole) -> Callable[..., User]:
    def checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this action",
            )
        return user

    return checker


RequireAdmin = Annotated[User, Depends(require_roles(UserRole.admin))]
RequireAnalystOrAdmin = Annotated[User, Depends(require_roles(UserRole.analyst, UserRole.admin))]
RequireAnyAuthenticated = Annotated[User, Depends(get_current_user)]
