"""College admin identity and organization collections (phase 2)."""

from datetime import date, datetime
from enum import Enum

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.roles import Role
from app.common.time import utcnow


class InstitutionAccountStatus(str, Enum):
    INVITED = "invited"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


class InvitationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REVOKED = "revoked"
    EXPIRED = "expired"


class OrganizationUnitType(str, Enum):
    SCHOOL = "school"
    FACULTY = "faculty"
    DIVISION = "division"


class DepartmentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class AccessHistoryEvent(str, Enum):
    USER_CREATED = "user_created"
    USER_INVITED = "user_invited"
    USER_ACTIVATED = "user_activated"
    USER_SUSPENDED = "user_suspended"
    USER_REACTIVATED = "user_reactivated"
    USER_DEACTIVATED = "user_deactivated"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REVOKED = "role_revoked"
    ROLE_CHANGED = "role_changed"
    SESSION_REVOKED = "session_revoked"
    PASSWORD_RESET = "password_reset"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    DEPARTMENT_TRANSFER = "department_transfer"


class InstitutionUser(Document):
    """Tenant-scoped user metadata (identity remains in `users`)."""

    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    campus_id: PydanticObjectId | None = None
    department_id: PydanticObjectId | None = None
    account_status: InstitutionAccountStatus = InstitutionAccountStatus.ACTIVE
    suspension_reason: str | None = Field(default=None, max_length=500)
    suspended_at: datetime | None = None
    faculty_profile_linked: bool = False
    student_profile_linked: bool = False
    employee_profile_linked: bool = False
    last_login_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_users"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING)],
                unique=True,
                name="unique_institution_user",
            ),
            IndexModel([("tenant_id", ASCENDING), ("account_status", ASCENDING)], name="institution_users_by_status"),
            IndexModel([("tenant_id", ASCENDING), ("department_id", ASCENDING)], name="institution_users_by_dept"),
        ]


class InstitutionRole(Document):
    tenant_id: PydanticObjectId
    role_code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    base_role: Role
    granted_permissions: list[str] = Field(default_factory=list)
    denied_permissions: list[str] = Field(default_factory=list)
    is_system: bool = False
    is_active: bool = True
    version: int = 1
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "institution_roles"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("role_code", ASCENDING)],
                unique=True,
                name="unique_institution_role_code",
            ),
        ]


class InstitutionPermission(Document):
    """Assignable permission catalogue per tenant (seeded from platform allowlist)."""

    tenant_id: PydanticObjectId
    permission_code: str
    description: str = ""
    assignable: bool = True
    category: str = "general"
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_permissions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("permission_code", ASCENDING)],
                unique=True,
                name="unique_institution_permission",
            ),
        ]


class InstitutionRoleAssignment(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    institution_role_id: PydanticObjectId
    assigned_by: PydanticObjectId | None = None
    assigned_at: datetime = Field(default_factory=utcnow)
    revoked_at: datetime | None = None

    class Settings:
        name = "institution_role_assignments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("institution_role_id", ASCENDING)],
                unique=True,
                name="unique_role_assignment",
                partialFilterExpression={"revoked_at": None},
            ),
            IndexModel([("tenant_id", ASCENDING), ("user_id", ASCENDING)], name="assignments_by_user"),
        ]


class InstitutionUserInvitation(Document):
    tenant_id: PydanticObjectId
    email: str
    full_name: str
    intended_role: Role
    department_id: PydanticObjectId | None = None
    campus_id: PydanticObjectId | None = None
    institution_role_id: PydanticObjectId | None = None
    token_hash: str
    status: InvitationStatus = InvitationStatus.PENDING
    expires_at: datetime
    accepted_at: datetime | None = None
    created_by: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_user_invitations"
        indexes = [
            IndexModel([("token_hash", ASCENDING)], unique=True, name="unique_institution_invite_token"),
            IndexModel(
                [("tenant_id", ASCENDING), ("email", ASCENDING), ("status", ASCENDING)],
                name="institution_invite_by_email",
            ),
            IndexModel([("expires_at", ASCENDING)], name="institution_invite_expiry"),
        ]


class InstitutionAccessHistory(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId | None = None
    event_type: AccessHistoryEvent
    actor_id: PydanticObjectId | None = None
    summary: str = Field(max_length=500)
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_access_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="access_history_by_user",
            ),
            IndexModel([("tenant_id", ASCENDING), ("created_at", DESCENDING)], name="access_history_by_tenant"),
        ]


class InstitutionOrganizationUnit(Document):
    tenant_id: PydanticObjectId
    unit_code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=200)
    unit_type: OrganizationUnitType
    parent_unit_id: PydanticObjectId | None = None
    campus_ids: list[PydanticObjectId] = Field(default_factory=list)
    status: DepartmentStatus = DepartmentStatus.ACTIVE
    head_user_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_organization_units"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("unit_code", ASCENDING)],
                unique=True,
                name="unique_org_unit_code",
            ),
            IndexModel([("tenant_id", ASCENDING), ("unit_type", ASCENDING)], name="org_units_by_type"),
        ]


class InstitutionDepartment(Document):
    tenant_id: PydanticObjectId
    department_code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=200)
    central_department_id: PydanticObjectId | None = None
    organization_unit_id: PydanticObjectId | None = None
    parent_department_id: PydanticObjectId | None = None
    campus_ids: list[PydanticObjectId] = Field(default_factory=list)
    status: DepartmentStatus = DepartmentStatus.ACTIVE
    head_user_id: PydanticObjectId | None = None
    reporting_to_department_id: PydanticObjectId | None = None
    programme_codes: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "institution_departments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("department_code", ASCENDING)],
                unique=True,
                name="unique_institution_department_code",
            ),
            IndexModel([("tenant_id", ASCENDING), ("parent_department_id", ASCENDING)], name="dept_by_parent"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="dept_by_status"),
        ]


class DepartmentHierarchy(Document):
    """Closure edges for fast ancestry checks (maintained on hierarchy changes)."""

    tenant_id: PydanticObjectId
    ancestor_id: PydanticObjectId
    descendant_id: PydanticObjectId
    depth: int = Field(ge=0)

    class Settings:
        name = "department_hierarchy"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("ancestor_id", ASCENDING), ("descendant_id", ASCENDING)],
                unique=True,
                name="unique_hierarchy_edge",
            ),
            IndexModel([("tenant_id", ASCENDING), ("descendant_id", ASCENDING)], name="hierarchy_descendants"),
        ]


class DepartmentHeadAssignment(Document):
    tenant_id: PydanticObjectId
    department_id: PydanticObjectId
    user_id: PydanticObjectId
    effective_from: date
    effective_to: date | None = None
    assigned_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_head_assignments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("department_id", ASCENDING), ("effective_from", DESCENDING)],
                name="dept_head_by_department",
            ),
        ]


class DepartmentStaffAssociation(Document):
    tenant_id: PydanticObjectId
    department_id: PydanticObjectId
    user_id: PydanticObjectId
    association_role: str = "staff"
    is_primary: bool = False
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_staff_associations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("department_id", ASCENDING), ("user_id", ASCENDING)],
                unique=True,
                name="unique_dept_staff_assoc",
            ),
        ]


class DepartmentHistory(Document):
    tenant_id: PydanticObjectId
    department_id: PydanticObjectId
    change_type: str
    snapshot: dict = Field(default_factory=dict)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("department_id", ASCENDING), ("created_at", DESCENDING)],
                name="department_history_by_dept",
            ),
        ]
