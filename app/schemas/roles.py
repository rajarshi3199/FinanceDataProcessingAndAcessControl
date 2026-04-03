from pydantic import BaseModel, Field

from app.models.user import UserRole


class RoleDefinition(BaseModel):
    role: UserRole
    label: str = Field(description="Human-readable name")
    description: str = Field(description="Capabilities summary")


ROLE_DEFINITIONS: list[RoleDefinition] = [
    RoleDefinition(
        role=UserRole.viewer,
        label="Viewer",
        description="Read-only dashboard summaries and aggregates; cannot access raw financial records.",
    ),
    RoleDefinition(
        role=UserRole.analyst,
        label="Analyst",
        description="Dashboard access plus read-only access to financial records, search, and analytics.",
    ),
    RoleDefinition(
        role=UserRole.admin,
        label="Administrator",
        description="Full access: manage users and all financial record operations.",
    ),
]
