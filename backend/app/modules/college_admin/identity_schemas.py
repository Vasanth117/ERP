"""College admin phase 2 API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from app.common.roles import Role
from app.modules.college_admin.identity_models import (
    DepartmentKind,
    DepartmentStatus,
    InstitutionAccountStatus,
    InstitutionDepartment,
    InstitutionOrganizationUnit,
    InstitutionRole,
    InstitutionUser,
    InvitationStatus,
    OrganizationUnitType,
)


class InstitutionUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=200)
    role: Role
    department_id: str | None = None
    campus_id: str | None = None


class InstitutionUserInvite(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=200)
    role: Role
    department_id: str | None = None
    campus_id: str | None = None
    institution_role_id: str | None = None


class InstitutionUserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    department_id: str | None = None
    campus_id: str | None = None


class InstitutionUserRead(BaseModel):
    user_id: str
    email: str
    full_name: str
    role: Role
    tenant_id: str
    department_id: str | None = None
    campus_id: str | None = None
    account_status: InstitutionAccountStatus
    is_active: bool
    institution_roles: list[str] = Field(default_factory=list)
    last_login_at: datetime | None = None
    created_at: datetime

    @classmethod
    def from_parts(
        cls,
        user,
        institution: InstitutionUser,
        institution_role_codes: list[str],
    ) -> "InstitutionUserRead":
        return cls(
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=str(user.tenant_id),
            department_id=str(user.department_id) if user.department_id else None,
            campus_id=str(institution.campus_id) if institution.campus_id else None,
            account_status=institution.account_status,
            is_active=user.is_active,
            institution_roles=institution_role_codes,
            last_login_at=institution.last_login_at,
            created_at=institution.created_at,
        )


class UserRoleAssign(BaseModel):
    role: Role | None = None
    institution_role_id: str | None = None


class UserRoleRevoke(BaseModel):
    institution_role_id: str


class AccountStatusChange(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class InvitationCreateResponse(BaseModel):
    invitation_id: str
    email: str
    expires_at: datetime
    status: InvitationStatus
    accept_token: str | None = Field(default=None, description="Returned only in non-production for testing")


class InvitationAccept(BaseModel):
    token: str = Field(min_length=16)
    password: str = Field(min_length=8, max_length=128)


class BulkUserCreate(BaseModel):
    users: list[InstitutionUserCreate] = Field(min_length=1, max_length=100)


class InstitutionRoleCreate(BaseModel):
    role_code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    base_role: Role
    granted_permissions: list[str] = Field(default_factory=list)
    denied_permissions: list[str] = Field(default_factory=list)
    role_settings: dict = Field(default_factory=dict)


class InstitutionRoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    granted_permissions: list[str] | None = None
    denied_permissions: list[str] | None = None
    role_settings: dict | None = None
    is_active: bool | None = None


class InstitutionRoleRead(BaseModel):
    role_id: str
    role_code: str
    name: str
    description: str | None
    base_role: Role
    granted_permissions: list[str]
    denied_permissions: list[str]
    role_settings: dict
    is_system: bool
    is_active: bool
    version: int

    @classmethod
    def from_document(cls, doc: InstitutionRole) -> "InstitutionRoleRead":
        return cls(
            role_id=str(doc.id),
            role_code=doc.role_code,
            name=doc.name,
            description=doc.description,
            base_role=doc.base_role,
            granted_permissions=doc.granted_permissions,
            denied_permissions=doc.denied_permissions,
            role_settings=doc.role_settings or {},
            is_system=doc.is_system,
            is_active=doc.is_active,
            version=doc.version,
        )


class PermissionRead(BaseModel):
    permission_code: str
    description: str
    assignable: bool
    category: str


class AccessHistoryRead(BaseModel):
    event_type: str
    summary: str
    user_id: str | None = None
    actor_id: str | None = None
    created_at: datetime
    metadata: dict = Field(default_factory=dict)


class OrganizationUnitCreate(BaseModel):
    unit_code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=200)
    unit_type: OrganizationUnitType
    parent_unit_id: str | None = None
    campus_ids: list[str] = Field(default_factory=list)
    head_user_id: str | None = None


class OrganizationUnitRead(BaseModel):
    unit_id: str
    unit_code: str
    name: str
    unit_type: OrganizationUnitType
    parent_unit_id: str | None
    campus_ids: list[str]
    status: DepartmentStatus
    head_user_id: str | None

    @classmethod
    def from_document(cls, doc: InstitutionOrganizationUnit) -> "OrganizationUnitRead":
        return cls(
            unit_id=str(doc.id),
            unit_code=doc.unit_code,
            name=doc.name,
            unit_type=doc.unit_type,
            parent_unit_id=str(doc.parent_unit_id) if doc.parent_unit_id else None,
            campus_ids=[str(cid) for cid in doc.campus_ids],
            status=doc.status,
            head_user_id=str(doc.head_user_id) if doc.head_user_id else None,
        )


class InstitutionDepartmentCreate(BaseModel):
    department_code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    department_kind: DepartmentKind = DepartmentKind.ACADEMIC
    establishment_year: int | None = Field(default=None, ge=1800, le=2100)
    building_floor_label: str | None = None
    contact_email: str | None = Field(default=None, max_length=320)
    approved_intake_ug: int | None = Field(default=None, ge=0)
    aicte_approval_reference: str | None = None
    cost_centre_code: str | None = None
    settings_template_department_id: str | None = None
    head_user_id: str | None = None
    organization_unit_id: str | None = None
    parent_department_id: str | None = None
    campus_ids: list[str] = Field(default_factory=list)
    programme_codes: list[str] = Field(default_factory=list)
    reporting_to_department_id: str | None = None
    status: DepartmentStatus | None = None


class InstitutionDepartmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    department_kind: DepartmentKind | None = None
    establishment_year: int | None = Field(default=None, ge=1800, le=2100)
    building_floor_label: str | None = None
    contact_email: str | None = Field(default=None, max_length=320)
    approved_intake_ug: int | None = Field(default=None, ge=0)
    aicte_approval_reference: str | None = None
    cost_centre_code: str | None = None
    settings_template_department_id: str | None = None
    organization_unit_id: str | None = None
    parent_department_id: str | None = None
    campus_ids: list[str] | None = None
    status: DepartmentStatus | None = None
    programme_codes: list[str] | None = None
    reporting_to_department_id: str | None = None


class InstitutionDepartmentRead(BaseModel):
    department_id: str
    department_code: str
    name: str
    description: str | None = None
    department_kind: DepartmentKind
    establishment_year: int | None = None
    building_floor_label: str | None = None
    contact_email: str | None = None
    approved_intake_ug: int | None = None
    aicte_approval_reference: str | None = None
    cost_centre_code: str | None = None
    settings_template_department_id: str | None = None
    central_department_id: str | None
    organization_unit_id: str | None
    parent_department_id: str | None
    campus_ids: list[str]
    status: DepartmentStatus
    head_user_id: str | None
    reporting_to_department_id: str | None
    programme_codes: list[str]
    updated_at: datetime

    @classmethod
    def from_document(cls, doc: InstitutionDepartment) -> "InstitutionDepartmentRead":
        return cls(
            department_id=str(doc.id),
            department_code=doc.department_code,
            name=doc.name,
            description=doc.description,
            department_kind=doc.department_kind,
            establishment_year=doc.establishment_year,
            building_floor_label=doc.building_floor_label,
            contact_email=doc.contact_email,
            approved_intake_ug=doc.approved_intake_ug,
            aicte_approval_reference=doc.aicte_approval_reference,
            cost_centre_code=doc.cost_centre_code,
            settings_template_department_id=(
                str(doc.settings_template_department_id) if doc.settings_template_department_id else None
            ),
            central_department_id=str(doc.central_department_id) if doc.central_department_id else None,
            organization_unit_id=str(doc.organization_unit_id) if doc.organization_unit_id else None,
            parent_department_id=str(doc.parent_department_id) if doc.parent_department_id else None,
            campus_ids=[str(cid) for cid in doc.campus_ids],
            status=doc.status,
            head_user_id=str(doc.head_user_id) if doc.head_user_id else None,
            reporting_to_department_id=str(doc.reporting_to_department_id) if doc.reporting_to_department_id else None,
            programme_codes=doc.programme_codes,
            updated_at=doc.updated_at,
        )


class DepartmentHeadAssign(BaseModel):
    user_id: str
    effective_from: datetime | None = None
    effective_to: date | None = None
    appointment_type: str = "regular"
    order_reference: str | None = Field(default=None, max_length=120)
    send_for_principal_approval: bool = False


class DepartmentTransfer(BaseModel):
    target_parent_department_id: str | None = None
    target_organization_unit_id: str | None = None
    reason: str | None = Field(default=None, max_length=500)


class DepartmentHistoryRead(BaseModel):
    change_type: str
    snapshot: dict
    created_at: datetime
    actor_id: str | None = None
