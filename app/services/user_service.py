from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.security import hash_password
from app.models.financial_record import FinancialRecord
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserSelfUpdate, UserUpdate


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalars(select(User).where(User.email == email)).first()


def list_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id).offset(skip).limit(limit)).all())


def create_user(db: Session, data: UserCreate) -> User:
    if get_by_email(db, data.email):
        raise ConflictError("Email already registered")
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_self(db: Session, user: User, data: UserSelfUpdate) -> User:
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.password is not None:
        user.hashed_password = hash_password(data.password)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int, actor: User) -> None:
    if actor.role != UserRole.admin:
        raise ForbiddenError("Only admins can delete users")
    if actor.id == user_id:
        raise ForbiddenError("Cannot delete your own account")
    target = get_by_id(db, user_id)
    if not target:
        raise NotFoundError("User not found")
    created = db.scalar(
        select(func.count(FinancialRecord.id)).where(FinancialRecord.created_by_id == user_id)
    ) or 0
    if created > 0:
        raise ConflictError("User has created financial records; deactivate instead or remove records first")
    db.delete(target)
    db.commit()


def update_user(db: Session, user_id: int, data: UserUpdate) -> User:
    user = get_by_id(db, user_id)
    if not user:
        raise NotFoundError("User not found")
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.password is not None:
        user.hashed_password = hash_password(data.password)
    db.commit()
    db.refresh(user)
    return user


def ensure_admin_exists(db: Session) -> None:
    """Bootstrap: create default admin if no users exist (development convenience)."""
    if (db.scalar(select(func.count(User.id))) or 0) > 0:
        return
    admin = User(
        email="admin@example.com",
        hashed_password=hash_password("adminpass123"),
        full_name="Default Admin",
        role=UserRole.admin,
    )
    db.add(admin)
    db.commit()
