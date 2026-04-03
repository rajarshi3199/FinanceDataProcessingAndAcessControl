from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import RequireAdmin, RequireAnyAuthenticated
from app.database import get_db
from app.schemas.user import UserCreate, UserOut, UserSelfUpdate, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def read_me(current: RequireAnyAuthenticated) -> UserOut:
    return UserOut.model_validate(current)


@router.patch("/me", response_model=UserOut)
def patch_me(
    body: UserSelfUpdate,
    current: RequireAnyAuthenticated,
    db: Session = Depends(get_db),
) -> UserOut:
    u = user_service.update_self(db, current, body)
    return UserOut.model_validate(u)


@router.post("", response_model=UserOut, status_code=201)
def create_user(
    body: UserCreate,
    _admin: RequireAdmin,
    db: Session = Depends(get_db),
) -> UserOut:
    user = user_service.create_user(db, body)
    return UserOut.model_validate(user)


@router.get("", response_model=list[UserOut])
def list_users(
    _admin: RequireAdmin,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> list[UserOut]:
    users = user_service.list_users(db, skip=skip, limit=limit)
    return [UserOut.model_validate(u) for u in users]


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    _admin: RequireAdmin,
    db: Session = Depends(get_db),
) -> UserOut:
    u = user_service.get_by_id(db, user_id)
    if not u:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("User not found")
    return UserOut.model_validate(u)


@router.patch("/{user_id}", response_model=UserOut)
def patch_user(
    user_id: int,
    body: UserUpdate,
    _admin: RequireAdmin,
    db: Session = Depends(get_db),
) -> UserOut:
    u = user_service.update_user(db, user_id, body)
    return UserOut.model_validate(u)


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    admin: RequireAdmin,
    db: Session = Depends(get_db),
) -> Response:
    user_service.delete_user(db, user_id, admin)
    return Response(status_code=204)
