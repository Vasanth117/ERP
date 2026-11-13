"""College, onboarding, and department payloads."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.modules.tenants.domain_utils import normalize_domain, normalize_tenant_code, validate_domain_format
from app.modules.tenants.enums import (
    InvitationStatus,
    OnboardingStage,
    TenantLifecycleStatus,
    TenantOperationalStatus,
)
from app.modules.tenants.models import Department, Tenant
from app.modules.tenants.platform_models import (
    AcademicSettings,
    InstitutionAddress,
    TenantAdminInvitation,
    TenantOnboarding,
    TenantProvisioningJob,
    TenantStatusHistory,
)


class NameCodeCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=2, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return normalize_tenant_code(value)


class AddressInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    line1: str = Field(min_length=1, max_length=300)
    line2: str | None = Field(default=None, max_length=300)
    city: str = Field(min_length=1, max_length=120)
    state: str = Field(min_length=1, max_length=120)
    country: str = Field(min_length=2, max_length=120)
    postal_code: str | None = Field(default=None, max_length=32)


class AcademicSettingsInput(BaseModel):
    default_academic_year_label: str | None = Field(default=None, max_length=64)
    grading_scheme: str | None = Field(default=None, max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CollegeAdminInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    full_name: str = Field(min_length=1, max_length=200)


class TenantRegisterCreate(BaseModel):
    """Full tenant registration for platform operators."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=2, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")
    institution_email: EmailStr
    contact_phone: str = Field(min_length=6, max_length=32)
    address: AddressInput
    institution_type: str = Field(min_length=2, max_length=64)
    timezone: str = Field(default="UTC", min_length=1, max_length=64)
    locale: str = Field(default="en-US", min_length=2, max_length=16)
    domain: str = Field(min_length=3, max_length=253)
    academic_settings: AcademicSettingsInput | None = None
    college_admin: CollegeAdminInput
    submit: bool = Field(
        default=True,
        description="When true, moves onboarding past draft and starts verification/provisioning.",
    )
    idempotency_key: str | None = Field(default=None, max_length=128)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return normalize_tenant_code(value)

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, value: str) -> str:
        if not validate_domain_format(value):
            raise ValueError("Invalid domain format")
        return normalize_domain(value)


class TenantCreate(NameCodeCreate):
    """Legacy minimal create (active tenant without onboarding workflow)."""

    pass


class TenantMetadataUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=200)
    institution_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, min_length=6, max_length=32)
    address: AddressInput | None = None
    institution_type: str | None = Field(default=None, min_length=2, max_length=64)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    locale: str | None = Field(default=None, min_length=2, max_length=16)
    academic_settings: AcademicSettingsInput | None = None


class TenantValidateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: str | None = Field(default=None, min_length=2, max_length=32)
    domain: str | None = Field(default=None, min_length=3, max_length=253)
    institution_email: EmailStr | None = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str | None) -> str | None:
        return normalize_tenant_code(value) if value else None

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not validate_domain_format(value):
            raise ValueError("Invalid domain format")
        return normalize_domain(value)


class AvailabilityResponse(BaseModel):
    available: bool
    normalized_value: str


class DepartmentCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=2, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")

    @field_validator("code")
    @classmethod
    def uppercase_code(cls, value: str) -> str:
        return value.upper()


class InstitutionAddressRead(BaseModel):
    line1: str
    line2: str | None
    city: str
    state: str
    country: str
    postal_code: str | None

    @classmethod
    def from_model(cls, address: InstitutionAddress) -> "InstitutionAddressRead":
        return cls(
            line1=address.line1,
            line2=address.line2,
            city=address.city,
            state=address.state,
            country=address.country,
            postal_code=address.postal_code,
        )


class AcademicSettingsRead(BaseModel):
    default_academic_year_label: str | None
    grading_scheme: str | None
    metadata: dict[str, Any]

    @classmethod
    def from_model(cls, settings: AcademicSettings) -> "AcademicSettingsRead":
        return cls(
            default_academic_year_label=settings.default_academic_year_label,
            grading_scheme=settings.grading_scheme,
            metadata=settings.metadata,
        )


class TenantRead(BaseModel):
    id: str
    name: str
    code: str
    status: TenantOperationalStatus
    lifecycle_status: TenantLifecycleStatus
    is_active: bool
    institution_email: str | None
    contact_phone: str | None
    address: InstitutionAddressRead
    institution_type: str | None
    timezone: str
    locale: str
    primary_domain: str | None
    academic_settings: AcademicSettingsRead
    activated_at: datetime | None
    suspended_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_document(cls, tenant: Tenant) -> "TenantRead":
        return cls(
            id=str(tenant.id),
            name=tenant.name,
            code=tenant.code,
            status=tenant.status,
            lifecycle_status=tenant.lifecycle_status,
            is_active=tenant.is_active,
            institution_email=tenant.institution_email,
            contact_phone=tenant.contact_phone,
            address=InstitutionAddressRead.from_model(tenant.address),
            institution_type=tenant.institution_type,
            timezone=tenant.timezone,
            locale=tenant.locale,
            primary_domain=tenant.primary_domain,
            academic_settings=AcademicSettingsRead.from_model(tenant.academic_settings),
            activated_at=tenant.activated_at,
            suspended_at=tenant.suspended_at,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at,
        )


class OnboardingStageHistoryItem(BaseModel):
    stage: OnboardingStage
    at: datetime
    actor_id: str | None = None
    note: str | None = None


class OnboardingStatusRead(BaseModel):
    tenant_id: str
    stage: OnboardingStage
    stage_history: list[OnboardingStageHistoryItem]
    started_at: datetime
    completed_at: datetime | None
    cancelled_at: datetime | None
    cancel_reason: str | None

    @classmethod
    def from_document(cls, onboarding: TenantOnboarding) -> "OnboardingStatusRead":
        history = [
            OnboardingStageHistoryItem(
                stage=OnboardingStage(item["stage"]),
                at=item["at"],
                actor_id=item.get("actor_id"),
                note=item.get("note"),
            )
            for item in onboarding.stage_history
        ]
        return cls(
            tenant_id=str(onboarding.tenant_id),
            stage=onboarding.stage,
            stage_history=history,
            started_at=onboarding.started_at,
            completed_at=onboarding.completed_at,
            cancelled_at=onboarding.cancelled_at,
            cancel_reason=onboarding.cancel_reason,
        )


class InvitationRead(BaseModel):
    id: str
    tenant_id: str
    email: str
    full_name: str
    status: InvitationStatus
    expires_at: datetime
    sent_count: int
    last_sent_at: datetime
    accepted_at: datetime | None

    @classmethod
    def from_document(cls, invitation: TenantAdminInvitation) -> "InvitationRead":
        return cls(
            id=str(invitation.id),
            tenant_id=str(invitation.tenant_id),
            email=invitation.email,
            full_name=invitation.full_name,
            status=invitation.status,
            expires_at=invitation.expires_at,
            sent_count=invitation.sent_count,
            last_sent_at=invitation.last_sent_at,
            accepted_at=invitation.accepted_at,
        )


class InvitationCreateResponse(BaseModel):
    invitation: InvitationRead
    token: str | None = Field(
        default=None,
        description="Returned once when created or resent; never stored in plaintext server-side.",
    )


class ProvisioningJobRead(BaseModel):
    id: str
    tenant_id: str
    idempotency_key: str
    status: str
    steps_completed: list[str]
    attempt_count: int
    last_error: str | None
    started_at: datetime | None
    finished_at: datetime | None

    @classmethod
    def from_document(cls, job: TenantProvisioningJob) -> "ProvisioningJobRead":
        return cls(
            id=str(job.id),
            tenant_id=str(job.tenant_id),
            idempotency_key=job.idempotency_key,
            status=job.status.value,
            steps_completed=[step.value for step in job.steps_completed],
            attempt_count=job.attempt_count,
            last_error=job.last_error,
            started_at=job.started_at,
            finished_at=job.finished_at,
        )


class TenantStatusHistoryRead(BaseModel):
    id: str
    from_status: str | None
    to_status: str
    reason: str | None
    actor_id: str | None
    created_at: datetime

    @classmethod
    def from_document(cls, entry: TenantStatusHistory) -> "TenantStatusHistoryRead":
        return cls(
            id=str(entry.id),
            from_status=entry.from_status,
            to_status=entry.to_status,
            reason=entry.reason,
            actor_id=str(entry.actor_id) if entry.actor_id else None,
            created_at=entry.created_at,
        )


class TenantRegistrationResult(BaseModel):
    tenant: TenantRead
    onboarding: OnboardingStatusRead
    provisioning_job: ProvisioningJobRead | None = None
    admin_invitation: InvitationCreateResponse | None = None


class DepartmentRead(BaseModel):
    id: str
    tenant_id: str
    name: str
    code: str
    is_active: bool
    created_at: datetime

    @classmethod
    def from_document(cls, department: Department) -> "DepartmentRead":
        return cls(
            id=str(department.id),
            tenant_id=str(department.tenant_id),
            name=department.name,
            code=department.code,
            is_active=department.is_active,
            created_at=department.created_at,
        )


class TenantValidationResult(BaseModel):
    valid: bool
    issues: list[dict[str, str]] = Field(default_factory=list)
