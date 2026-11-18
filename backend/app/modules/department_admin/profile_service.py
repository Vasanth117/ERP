"""Department profile, settings, and change-request workflows."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.department_admin.audit_helpers import record_department_audit
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicYear
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.modules.department_admin.dashboard_service import _head_summary
from app.modules.department_admin.models import (
    DepartmentProfileChangeRequest,
    DepartmentProfileChangeStatus,
    DepartmentProfileDetails,
    DepartmentSetting,
    DepartmentSettingHistory,
)
from app.modules.department_admin.policy import resolve_authorized_department
from app.modules.department_admin.schemas import (
    SENSITIVE_PROFILE_FIELDS,
    DepartmentAcademicConfigVisibilityRead,
    DepartmentProfileChangeRequestCreate,
    DepartmentProfileChangeRequestRead,
    DepartmentProfileDetailsRead,
    DepartmentProfileDetailsUpdate,
    DepartmentSettingRead,
    DepartmentSettingUpdate,
    normalize_profile_field,
)
from app.modules.department_admin.settings_registry import validate_department_setting
from app.modules.attendance.models import AttendancePolicyReference


async def _ensure_profile_details(
    tenant_id: PydanticObjectId,
    institution: InstitutionDepartment,
    central_id: PydanticObjectId,
) -> DepartmentProfileDetails:
    doc = await DepartmentProfileDetails.find_one(
        Eq(DepartmentProfileDetails.tenant_id, tenant_id),
        Eq(DepartmentProfileDetails.institution_department_id, institution.id),
    )
    if doc is not None:
        return doc
    doc = DepartmentProfileDetails(
        tenant_id=tenant_id,
        institution_department_id=institution.id,
        central_department_id=central_id,
    )
    await doc.insert()
    return doc


async def get_department_profile(scope: AccessScope, user: User) -> DepartmentProfileDetailsRead:
    authorize(scope, Permission.DEPARTMENT_PROFILE_READ)
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    details = await _ensure_profile_details(tenant_id, institution, central_id)
    return DepartmentProfileDetailsRead(
        institution_department_id=str(institution.id),
        department_code=institution.department_code,
        department_name=institution.name,
        status=institution.status,
        description=details.description,
        contact_email=details.contact_email,
        contact_phone=details.contact_phone,
        office_location=details.office_location,
        website_url=details.website_url,
        programme_codes=institution.programme_codes,
        head_of_department=await _head_summary(tenant_id, institution.head_user_id),
        revision=details.revision,
        updated_at=details.updated_at,
    )


async def update_department_profile(
    scope: AccessScope,
    user: User,
    payload: DepartmentProfileDetailsUpdate,
) -> DepartmentProfileDetailsRead:
    authorize(scope, Permission.DEPARTMENT_PROFILE_UPDATE)
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    details = await _ensure_profile_details(tenant_id, institution, central_id)
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        return await get_department_profile(scope, user)
    for field, value in updates.items():
        setattr(details, field, value)
    details.revision += 1
    details.updated_at = utcnow()
    details.updated_by = user.id
    await details.save()
    await record_department_audit(
        actor_id=user.id,
        action="department.profile.update",
        resource_type="department",
        resource_id=str(central_id),
        tenant_id=tenant_id,
        central_department_id=central_id,
        metadata={"fields": list(updates.keys())},
    )
    return await get_department_profile(scope, user)


async def list_department_settings(scope: AccessScope, user: User) -> list[DepartmentSettingRead]:
    authorize(scope, Permission.DEPARTMENT_SETTINGS_READ)
    _, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    rows = await DepartmentSetting.find(
        Eq(DepartmentSetting.tenant_id, tenant_id),
        Eq(DepartmentSetting.institution_department_id, institution.id),
    ).to_list()
    return [
        DepartmentSettingRead(
            key=row.setting_key,
            value=row.setting_value,
            category=row.category,
            revision=row.revision,
            updated_at=row.updated_at,
        )
        for row in rows
    ]


async def get_department_setting(scope: AccessScope, user: User, setting_key: str) -> DepartmentSettingRead:
    authorize(scope, Permission.DEPARTMENT_SETTINGS_READ)
    _, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    row = await DepartmentSetting.find_one(
        Eq(DepartmentSetting.tenant_id, tenant_id),
        Eq(DepartmentSetting.institution_department_id, institution.id),
        Eq(DepartmentSetting.setting_key, setting_key),
    )
    if row is None:
        raise AppError(code="NOT_FOUND", message="Setting not found", status_code=404)
    return DepartmentSettingRead(
        key=row.setting_key,
        value=row.setting_value,
        category=row.category,
        revision=row.revision,
        updated_at=row.updated_at,
    )


async def upsert_department_setting(
    scope: AccessScope,
    user: User,
    setting_key: str,
    payload: DepartmentSettingUpdate,
) -> DepartmentSettingRead:
    authorize(scope, Permission.DEPARTMENT_SETTINGS_MANAGE)
    _, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    try:
        value = validate_department_setting(setting_key, payload.value)
    except ValueError as exc:
        raise AppError(code="VALIDATION_ERROR", message=str(exc), status_code=422) from exc
    row = await DepartmentSetting.find_one(
        Eq(DepartmentSetting.tenant_id, tenant_id),
        Eq(DepartmentSetting.institution_department_id, institution.id),
        Eq(DepartmentSetting.setting_key, setting_key),
    )
    previous = row.setting_value if row is not None else None
    if row is None:
        row = DepartmentSetting(
            tenant_id=tenant_id,
            institution_department_id=institution.id,
            setting_key=setting_key,
            setting_value=value,
        )
        await row.insert()
    else:
        row.setting_value = value
        row.revision += 1
        row.updated_at = utcnow()
        row.updated_by = user.id
        await row.save()
    await DepartmentSettingHistory(
        tenant_id=tenant_id,
        institution_department_id=institution.id,
        setting_key=setting_key,
        previous_value=previous,
        new_value=value,
        changed_by=user.id,
    ).insert()
    await record_department_audit(
        actor_id=user.id,
        action="department.settings.update",
        resource_type="department_setting",
        resource_id=setting_key,
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return DepartmentSettingRead(
        key=row.setting_key,
        value=row.setting_value,
        category=row.category,
        revision=row.revision,
        updated_at=row.updated_at,
    )


async def create_profile_change_request(
    scope: AccessScope,
    user: User,
    payload: DepartmentProfileChangeRequestCreate,
) -> DepartmentProfileChangeRequestRead:
    authorize(scope, Permission.DEPARTMENT_PROFILE_UPDATE)
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    field_name = normalize_profile_field(payload.field_name)
    if field_name not in SENSITIVE_PROFILE_FIELDS:
        raise AppError(
            code="VALIDATION_ERROR",
            message=f"Field {field_name} can be updated directly or is not eligible for change requests",
            status_code=422,
        )
    if payload.idempotency_key:
        existing = await DepartmentProfileChangeRequest.find_one(
            Eq(DepartmentProfileChangeRequest.tenant_id, tenant_id),
            Eq(DepartmentProfileChangeRequest.idempotency_key, payload.idempotency_key),
        )
        if existing is not None:
            return _change_request_read(existing)
    previous_value: str | None = None
    if field_name == "name":
        previous_value = institution.name
    elif field_name == "department_code":
        previous_value = institution.department_code
    elif field_name == "status":
        previous_value = institution.status.value
    elif field_name == "head_user_id":
        previous_value = str(institution.head_user_id) if institution.head_user_id else None
        from app.common.ids import to_object_id
        from app.common.roles import Role

        try:
            head_id = to_object_id(payload.proposed_value, "proposed_value")
        except AppError as exc:
            raise AppError(code="VALIDATION_ERROR", message="Invalid head user id", status_code=422) from exc
        head_user = await User.get(head_id)
        if head_user is None or head_user.tenant_id != tenant_id or head_user.role != Role.FACULTY:
            raise AppError(
                code="VALIDATION_ERROR",
                message="Head must be an active faculty user in this college",
                status_code=422,
            )
        if head_user.department_id != central_id:
            raise AppError(code="VALIDATION_ERROR", message="Head must belong to this department", status_code=422)
    doc = DepartmentProfileChangeRequest(
        tenant_id=tenant_id,
        institution_department_id=institution.id,
        field_name=field_name,
        previous_value=previous_value,
        proposed_value=payload.proposed_value,
        requested_by=user.id,
        idempotency_key=payload.idempotency_key,
    )
    await doc.insert()
    await record_department_audit(
        actor_id=user.id,
        action="department.profile.change_request",
        resource_type="department",
        resource_id=str(central_id),
        tenant_id=tenant_id,
        central_department_id=central_id,
        metadata={"field": field_name},
    )
    return _change_request_read(doc)


def _change_request_read(doc: DepartmentProfileChangeRequest) -> DepartmentProfileChangeRequestRead:
    return DepartmentProfileChangeRequestRead(
        request_id=str(doc.id),
        field_name=doc.field_name,
        previous_value=doc.previous_value,
        proposed_value=doc.proposed_value,
        status=doc.status,
        requested_by=str(doc.requested_by),
        decided_by=str(doc.decided_by) if doc.decided_by else None,
        decided_at=doc.decided_at,
        rejection_reason=doc.rejection_reason,
        created_at=doc.created_at,
    )


async def list_profile_change_requests(
    scope: AccessScope,
    user: User,
    *,
    pagination: Pagination,
) -> Page[DepartmentProfileChangeRequestRead]:
    authorize(scope, Permission.DEPARTMENT_PROFILE_READ)
    _, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    query = DepartmentProfileChangeRequest.find(
        Eq(DepartmentProfileChangeRequest.tenant_id, tenant_id),
        Eq(DepartmentProfileChangeRequest.institution_department_id, institution.id),
    )
    total = await query.count()
    rows = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[_change_request_read(row) for row in rows],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def get_profile_change_request(scope: AccessScope, user: User, request_id: str) -> DepartmentProfileChangeRequestRead:
    authorize(scope, Permission.DEPARTMENT_PROFILE_READ)
    _, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    from app.common.ids import to_object_id

    doc = await DepartmentProfileChangeRequest.get(to_object_id(request_id, "request_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.institution_department_id != institution.id:
        raise AppError(code="NOT_FOUND", message="Change request not found", status_code=404)
    return _change_request_read(doc)


async def get_academic_config_visibility(scope: AccessScope, user: User) -> DepartmentAcademicConfigVisibilityRead:
    authorize(scope, Permission.DEPARTMENT_ACADEMIC_CONFIG_READ)
    _, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-created_at").limit(20).to_list()
    attendance_policy = await AttendancePolicyReference.find_one(
        Eq(AttendancePolicyReference.tenant_id, tenant_id),
        Eq(AttendancePolicyReference.is_active, True),
    )
    return DepartmentAcademicConfigVisibilityRead(
        academic_years=[
            {
                "label": row.label,
                "start_date": row.start_date.isoformat() if row.start_date else None,
                "end_date": row.end_date.isoformat() if row.end_date else None,
                "is_current": row.is_current,
            }
            for row in years
        ],
        attendance_policy_available=attendance_policy is not None,
        examination_policies_note="Examination policies are managed by college administration; department admins have read-only visibility in Phase 1.",
        grading_config_note="Grading configuration is college-controlled.",
        timetable_rules_note="Timetable rules are college-controlled.",
    )