"""College, onboarding, and department operations."""

from beanie import PydanticObjectId

from app.api.deps import AccessScope, assert_tenant_access
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.models import AuditLog
from app.modules.audit.service import record_audit
from app.modules.tenants.domain_utils import normalize_domain, normalize_tenant_code
from app.modules.tenants.enums import OnboardingStage, TenantLifecycleStatus, TenantOperationalStatus
from app.modules.tenants.invitation_service import create_admin_invitation, resend_admin_invitation
from app.modules.tenants.models import Department, Tenant
from app.modules.tenants.onboarding_service import (
    advance_onboarding_stage,
    cancel_onboarding,
    create_onboarding_record,
)
from app.modules.tenants.platform_models import AcademicSettings, InstitutionAddress, TenantOnboarding
from app.modules.tenants.provisioning_service import retry_failed_provisioning, run_provisioning
from app.modules.tenants.schemas import (
    AvailabilityResponse,
    DepartmentCreate,
    DepartmentRead,
    InvitationCreateResponse,
    InvitationRead,
    OnboardingStatusRead,
    ProvisioningJobRead,
    TenantCreate,
    TenantMetadataUpdate,
    TenantRead,
    TenantRegisterCreate,
    TenantRegistrationResult,
    TenantStatusHistoryRead,
    TenantValidateRequest,
    TenantValidationResult,
)
from app.repositories.platform_repository import (
    DomainRepository,
    OnboardingRepository,
    ProvisioningRepository,
    StatusHistoryRepository,
)
from app.repositories.tenant_repository import TenantRepository

_tenant_repo = TenantRepository()
_onboarding_repo = OnboardingRepository()
_domain_repo = DomainRepository()
_provisioning_repo = ProvisioningRepository()
_status_history_repo = StatusHistoryRepository()


def _address_from_input(payload: TenantRegisterCreate | TenantMetadataUpdate) -> InstitutionAddress | None:
    if not hasattr(payload, "address") or payload.address is None:
        return None
    address = payload.address
    return InstitutionAddress(
        line1=address.line1,
        line2=address.line2,
        city=address.city,
        state=address.state,
        country=address.country,
        postal_code=address.postal_code,
    )


async def create_tenant(scope: AccessScope, payload: TenantCreate) -> TenantRead:
    authorize(scope, Permission.PLATFORM_TENANT_MANAGE)
    existing = await _tenant_repo.find_tenant_by_code(payload.code)
    if existing is not None:
        raise AppError(
            code="CONFLICT",
            message="A college with this code already exists",
            status_code=409,
        )
    tenant = Tenant(
        name=payload.name,
        code=normalize_tenant_code(payload.code),
        status=TenantOperationalStatus.ACTIVE,
        lifecycle_status=TenantLifecycleStatus.ACTIVE,
        is_active=True,
        activated_at=utcnow(),
    )
    await tenant.insert()
    await _status_history_repo.append(
        tenant_id=tenant.id,
        from_status=None,
        to_status=tenant.status.value,
        actor_id=scope.user_id,
        reason="legacy_minimal_create",
    )
    await record_audit(
        actor_id=scope.user_id,
        action="tenant.created",
        resource_type="tenant",
        resource_id=str(tenant.id),
        tenant_id=tenant.id,
        metadata={"code": tenant.code, "mode": "minimal"},
    )
    return TenantRead.from_document(tenant)


async def register_tenant(scope: AccessScope, payload: TenantRegisterCreate) -> TenantRegistrationResult:
    authorize(scope, Permission.PLATFORM_TENANT_MANAGE)

    existing = await _tenant_repo.find_tenant_by_code(payload.code)
    if existing is not None:
        raise AppError(code="CONFLICT", message="A college with this code already exists", status_code=409)

    normalized_domain = normalize_domain(payload.domain)
    domain_taken = await _domain_repo.find_by_normalized(normalized_domain)
    if domain_taken is not None:
        raise AppError(code="CONFLICT", message="Domain is already registered", status_code=409)

    academic = payload.academic_settings
    tenant = Tenant(
        name=payload.name,
        code=normalize_tenant_code(payload.code),
        status=TenantOperationalStatus.ONBOARDING,
        lifecycle_status=TenantLifecycleStatus.PENDING,
        is_active=False,
        institution_email=str(payload.institution_email).lower(),
        contact_phone=payload.contact_phone,
        address=_address_from_input(payload) or InstitutionAddress(),
        institution_type=payload.institution_type,
        timezone=payload.timezone,
        locale=payload.locale,
        primary_domain=normalized_domain,
        academic_settings=AcademicSettings(
            default_academic_year_label=academic.default_academic_year_label if academic else None,
            grading_scheme=academic.grading_scheme if academic else None,
            metadata=academic.metadata if academic else {},
        ),
    )
    await tenant.insert()
    onboarding = await create_onboarding_record(tenant.id)
    await _status_history_repo.append(
        tenant_id=tenant.id,
        from_status=None,
        to_status=tenant.status.value,
        actor_id=scope.user_id,
        reason="registered",
    )

    invitation_response: InvitationCreateResponse | None = None
    provisioning_job: ProvisioningJobRead | None = None

    if payload.submit:
        onboarding = await advance_onboarding_stage(
            onboarding, OnboardingStage.SUBMITTED, actor_id=scope.user_id, note="submitted"
        )
        onboarding = await advance_onboarding_stage(
            onboarding,
            OnboardingStage.VERIFICATION_PENDING,
            actor_id=scope.user_id,
            note="auto_verification_queue",
        )
        onboarding = await advance_onboarding_stage(
            onboarding,
            OnboardingStage.VERIFIED,
            actor_id=scope.user_id,
            note="auto_verified",
        )
        job, token = await run_provisioning(
            tenant=tenant,
            onboarding=onboarding,
            actor_id=scope.user_id,
            domain=payload.domain,
            admin_email=str(payload.college_admin.email),
            admin_full_name=payload.college_admin.full_name,
            idempotency_key=payload.idempotency_key,
        )
        provisioning_job = ProvisioningJobRead.from_document(job)
        if token is not None:
            from app.repositories.platform_repository import InvitationRepository

            inv = await InvitationRepository().get_active_for_tenant(tenant.id)
            if inv is not None:
                invitation_response = InvitationCreateResponse(
                    invitation=InvitationRead.from_document(inv),
                    token=token,
                )

    await record_audit(
        actor_id=scope.user_id,
        action="tenant.registered",
        resource_type="tenant",
        resource_id=str(tenant.id),
        tenant_id=tenant.id,
        metadata={"code": tenant.code, "domain": normalized_domain},
    )
    onboarding = await _onboarding_repo.get_by_tenant(tenant.id)
    assert onboarding is not None
    return TenantRegistrationResult(
        tenant=TenantRead.from_document(tenant),
        onboarding=OnboardingStatusRead.from_document(onboarding),
        provisioning_job=provisioning_job,
        admin_invitation=invitation_response,
    )


async def validate_tenant_registration(payload: TenantValidateRequest) -> TenantValidationResult:
    issues: list[dict[str, str]] = []
    if payload.code:
        if await _tenant_repo.find_tenant_by_code(payload.code):
            issues.append({"field": "code", "message": "Tenant code is already taken"})
    if payload.domain:
        normalized = normalize_domain(payload.domain)
        if await _domain_repo.find_by_normalized(normalized):
            issues.append({"field": "domain", "message": "Domain is already registered"})
    return TenantValidationResult(valid=not issues, issues=issues)


async def check_tenant_code_availability(code: str) -> AvailabilityResponse:
    normalized = normalize_tenant_code(code)
    taken = await _tenant_repo.find_tenant_by_code(normalized)
    return AvailabilityResponse(available=taken is None, normalized_value=normalized)


async def check_domain_availability(domain: str) -> AvailabilityResponse:
    normalized = normalize_domain(domain)
    taken = await _domain_repo.find_by_normalized(normalized)
    return AvailabilityResponse(available=taken is None, normalized_value=normalized)


async def list_tenants(
    pagination: Pagination,
    *,
    status: TenantOperationalStatus | None = None,
) -> Page[TenantRead]:
    from app.repositories.platform_repository import PlatformTenantRepository

    repo = PlatformTenantRepository()
    total = await repo.count_tenants_filtered(status=status)
    documents = await repo.list_tenants_filtered(
        skip=pagination.offset,
        limit=pagination.limit,
        status=status,
    )
    return Page(
        items=[TenantRead.from_document(document) for document in documents],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def get_tenant(scope: AccessScope, tenant_id: PydanticObjectId) -> TenantRead:
    authorize(scope, Permission.TENANT_READ)
    assert_tenant_access(scope, tenant_id)
    tenant = await _tenant_repo.get_tenant(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
    return TenantRead.from_document(tenant)


async def update_tenant_metadata(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    payload: TenantMetadataUpdate,
) -> TenantRead:
    authorize(scope, Permission.PLATFORM_TENANT_MANAGE)
    tenant = await _tenant_repo.get_tenant(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)

    if payload.name is not None:
        tenant.name = payload.name
    if payload.institution_email is not None:
        tenant.institution_email = str(payload.institution_email).lower()
    if payload.contact_phone is not None:
        tenant.contact_phone = payload.contact_phone
    if payload.address is not None:
        tenant.address = _address_from_input(payload) or tenant.address
    if payload.institution_type is not None:
        tenant.institution_type = payload.institution_type
    if payload.timezone is not None:
        tenant.timezone = payload.timezone
    if payload.locale is not None:
        tenant.locale = payload.locale
    if payload.academic_settings is not None:
        tenant.academic_settings = AcademicSettings(
            default_academic_year_label=payload.academic_settings.default_academic_year_label,
            grading_scheme=payload.academic_settings.grading_scheme,
            metadata=payload.academic_settings.metadata,
        )
    tenant.updated_at = utcnow()
    await tenant.save()
    await record_audit(
        actor_id=scope.user_id,
        action="tenant.updated",
        resource_type="tenant",
        resource_id=str(tenant.id),
        tenant_id=tenant.id,
    )
    return TenantRead.from_document(tenant)


async def get_onboarding_status(scope: AccessScope, tenant_id: PydanticObjectId) -> OnboardingStatusRead:
    authorize(scope, Permission.PLATFORM_TENANT_READ)
    onboarding = await _onboarding_repo.get_by_tenant(tenant_id)
    if onboarding is None:
        raise AppError(code="NOT_FOUND", message="Onboarding record not found", status_code=404)
    return OnboardingStatusRead.from_document(onboarding)


async def get_onboarding_history(scope: AccessScope, tenant_id: PydanticObjectId) -> list[OnboardingStatusRead]:
    status = await get_onboarding_status(scope, tenant_id)
    return [status]


async def get_tenant_activity(scope: AccessScope, tenant_id: PydanticObjectId) -> list[TenantStatusHistoryRead]:
    authorize(scope, Permission.PLATFORM_TENANT_READ)
    history = await _status_history_repo.list_for_tenant(tenant_id)
    audits = (
        await AuditLog.find({"tenant_id": tenant_id})
        .sort("-created_at")
        .limit(50)
        .to_list()
    )
    combined: list[TenantStatusHistoryRead] = [TenantStatusHistoryRead.from_document(h) for h in history]
    for audit in audits:
        combined.append(
            TenantStatusHistoryRead(
                id=str(audit.id),
                from_status=None,
                to_status=audit.action,
                reason=audit.outcome,
                actor_id=str(audit.actor_id) if audit.actor_id else None,
                created_at=audit.created_at,
            )
        )
    combined.sort(key=lambda item: item.created_at, reverse=True)
    return combined[:50]


async def retry_tenant_provisioning(scope: AccessScope, tenant_id: PydanticObjectId) -> TenantRegistrationResult:
    authorize(scope, Permission.PLATFORM_TENANT_MANAGE)
    tenant = await _tenant_repo.get_tenant(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
    onboarding = await _onboarding_repo.get_by_tenant(tenant_id)
    if onboarding is None:
        raise AppError(code="NOT_FOUND", message="Onboarding record not found", status_code=404)
    if tenant.institution_email is None or tenant.primary_domain is None:
        raise AppError(code="CONFLICT", message="Tenant is missing provisioning metadata", status_code=409)

    from app.repositories.platform_repository import InvitationRepository

    active_invite = await InvitationRepository().get_active_for_tenant(tenant.id)
    admin_email = active_invite.email if active_invite else (tenant.institution_email or "")
    admin_name = active_invite.full_name if active_invite else "College Administrator"
    job, token = await retry_failed_provisioning(
        tenant=tenant,
        onboarding=onboarding,
        actor_id=scope.user_id,
        domain=tenant.primary_domain,
        admin_email=admin_email,
        admin_full_name=admin_name,
    )
    invitation_response: InvitationCreateResponse | None = None
    if token is not None:
        from app.repositories.platform_repository import InvitationRepository

        inv = await InvitationRepository().get_active_for_tenant(tenant.id)
        if inv is not None:
            invitation_response = InvitationCreateResponse(
                invitation=InvitationRead.from_document(inv),
                token=token,
            )
    onboarding = await _onboarding_repo.get_by_tenant(tenant_id)
    assert onboarding is not None
    return TenantRegistrationResult(
        tenant=TenantRead.from_document(tenant),
        onboarding=OnboardingStatusRead.from_document(onboarding),
        provisioning_job=ProvisioningJobRead.from_document(job),
        admin_invitation=invitation_response,
    )


async def initiate_admin_invitation(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    *,
    email: str,
    full_name: str,
) -> InvitationCreateResponse:
    authorize(scope, Permission.PLATFORM_TENANT_MANAGE)
    tenant = await _tenant_repo.get_tenant(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
    invitation, token = await create_admin_invitation(
        tenant_id=tenant_id,
        email=email,
        full_name=full_name,
        actor_id=scope.user_id,
    )
    return InvitationCreateResponse(invitation=InvitationRead.from_document(invitation), token=token)


async def resend_admin_invitation_route(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
) -> InvitationCreateResponse:
    authorize(scope, Permission.PLATFORM_TENANT_MANAGE)
    invitation, token = await resend_admin_invitation(tenant_id=tenant_id, actor_id=scope.user_id)
    return InvitationCreateResponse(invitation=InvitationRead.from_document(invitation), token=token)


async def cancel_tenant_onboarding(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    *,
    reason: str,
) -> OnboardingStatusRead:
    authorize(scope, Permission.PLATFORM_TENANT_MANAGE)
    tenant = await _tenant_repo.get_tenant(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
    onboarding = await _onboarding_repo.get_by_tenant(tenant_id)
    if onboarding is None:
        raise AppError(code="NOT_FOUND", message="Onboarding record not found", status_code=404)
    onboarding = await cancel_onboarding(onboarding, actor_id=scope.user_id, reason=reason)
    from app.modules.tenants.lifecycle_sync import apply_lifecycle_to_tenant

    apply_lifecycle_to_tenant(tenant, TenantLifecycleStatus.CLOSED)
    tenant.updated_at = utcnow()
    await tenant.save()
    await record_audit(
        actor_id=scope.user_id,
        action="tenant.onboarding.cancelled",
        resource_type="tenant",
        resource_id=str(tenant.id),
        tenant_id=tenant.id,
        metadata={"reason": reason},
    )
    return OnboardingStatusRead.from_document(onboarding)


async def get_latest_provisioning_job(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
) -> ProvisioningJobRead:
    authorize(scope, Permission.PLATFORM_TENANT_READ)
    jobs = await _provisioning_repo.latest_job(tenant_id)
    if jobs is None:
        raise AppError(code="NOT_FOUND", message="No provisioning job found", status_code=404)
    return ProvisioningJobRead.from_document(jobs)


async def _require_active_tenant(scope: AccessScope, tenant_id: PydanticObjectId) -> Tenant:
    assert_tenant_access(scope, tenant_id)
    tenant = await _tenant_repo.get_tenant(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
    if not tenant.is_active:
        raise AppError(code="TENANT_INACTIVE", message="This college is inactive", status_code=409)
    return tenant


async def create_department(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    payload: DepartmentCreate,
) -> DepartmentRead:
    authorize(scope, Permission.TENANT_DEPARTMENT_MANAGE)
    await _require_active_tenant(scope, tenant_id)
    existing = await _tenant_repo.find_department_by_code(tenant_id, payload.code)
    if existing is not None:
        raise AppError(
            code="CONFLICT",
            message="A department with this code already exists in this college",
            status_code=409,
        )
    department = Department(tenant_id=tenant_id, name=payload.name, code=payload.code)
    await department.insert()
    await record_audit(
        actor_id=scope.user_id,
        action="department.created",
        resource_type="department",
        resource_id=str(department.id),
        tenant_id=tenant_id,
        metadata={"code": department.code},
    )
    return DepartmentRead.from_document(department)


async def list_departments(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    pagination: Pagination,
) -> Page[DepartmentRead]:
    authorize(scope, Permission.TENANT_DEPARTMENT_READ)
    assert_tenant_access(scope, tenant_id)
    tenant = await _tenant_repo.get_tenant(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
    total = await _tenant_repo.count_departments(tenant_id)
    documents = await _tenant_repo.list_departments(
        tenant_id,
        skip=pagination.offset,
        limit=pagination.limit,
    )
    return Page(
        items=[DepartmentRead.from_document(document) for document in documents],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )
