from fastapi import APIRouter

from app.api.deps import RequireAnyAuthenticated
from app.schemas.roles import ROLE_DEFINITIONS, RoleDefinition

router = APIRouter(prefix="/meta", tags=["metadata"])


@router.get("/roles", response_model=list[RoleDefinition])
def list_roles(_user: RequireAnyAuthenticated) -> list[RoleDefinition]:
    """Describe available roles and typical permissions (for UI or onboarding)."""
    return ROLE_DEFINITIONS
