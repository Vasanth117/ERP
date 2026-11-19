"""HR employee profile management."""

import re

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.roles import Role
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentHistory, FacultyEmploymentStatus, FacultyRecord
from app.modules.college_admin.hr_admin_models import EmployeeOffboardingRecord
from app.modules.college_admin.identity_models import InstitutionAccountStatus, InstitutionUser
from app.modules.college_admin.models import InstitutionCampus
from app.modules.hr.employee_profile_models import HrEmployeeProfile, HrEmployeeProfileChangeLog, HrEmployeeProfileCorrectionRequest
from app.modules.hr.employee_profile_schemas import (
    EmployeeListItem,
    EmployeeProfileRead,
    EmployeeProfileUpdate,
    EmployeeRegister,
    EmployeeSearchQuery,
    EmploymentStatusChange,
    ProfileChangeHistoryItem,
    ProfileCorrectionRead,
    ProfileCorrectionReview,
    ProfileCorrectionSubmit,
    ProfileVerificationDecision,
)
from app.modules.hr.assignment_sync import ensure_current_assignment
from app.modules.hr.employee_sync import log_hr_activity, sync_employee_snapshot
from app.modules.hr.enums import OFFBOARDING_REQUIRED_STATUSES, HrStaffActivityType, ProfileCorrectionStatus, ProfileVerificationStatus
from app.modules.hr.policy import authorize_hr_employee_manage, authorize_hr_employee_read, require_hr_tenant_scope
from app.modules.hr.profile_completion import apply_completion_status
from app.modules.tenants.models import Department
from app.repositories.user_repository import UserRepository

_user_repo = UserRepository()
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PROTECTED_EMPLOYMENT_FIELDS = frozenset({"employment_status"})
_EMPLOYEE_CREATABLE_ROLES = frozenset(
    {
        Role.HR_STAFF,
        Role.ACCOUNTS_STAFF,
        Role.FINANCE_STAFF,
        Role.LIBRARIAN,
        Role.HOSTEL_ADMIN,
        Role.EXAMINATION_CELL,
    }
)


async def _validate_department(tenant_id: PydanticObjectId, department_id: PydanticObjectId) -> Department:
    dept = await Department.get(department_id)
    if dept is None or dept.tenant_id != tenant_id:
        raise AppError(code="VALIDATION_ERROR", message="Invalid department", status_code=422)
    return dept


async def _validate_campus(tenant_id: PydanticObjectId, campus_id: PydanticObjectId | None) -> None:
    if campus_id is None:
        return
    campus = await InstitutionCampus.get(campus_id)
    if campus is None or campus.tenant_id != tenant_id or not campus.is_active:
        raise AppError(code="VALIDATION_ERROR", message="Invalid campus", status_code=422)


async def _validate_manager(tenant_id: PydanticObjectId, manager_id: PydanticObjectId | None) -> None:
    if manager_id is None:
        return
    user = await _user_repo.get(manager_id)
    if user is None or user.tenant_id != tenant_id:
        raise AppError(code="VALIDATION_ERROR", message="Invalid reporting manager", status_code=422)
    employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, manager_id))
    if employee is None:
        raise AppError(code="VALIDATION_ERROR", message="Reporting manager must be an employee", status_code=422)


async def _ensure_institution_user(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    department_id: PydanticObjectId | None,
    campus_id: PydanticObjectId | None,
) -> InstitutionUser:
    doc = await InstitutionUser.find_one(Eq(InstitutionUser.tenant_id, tenant_id), Eq(InstitutionUser.user_id, user_id))
    if doc is None:
        doc = InstitutionUser(
            tenant_id=tenant_id,
            user_id=user_id,
            department_id=department_id,
            campus_id=campus_id,
            employee_profile_linked=True,
        )
        await doc.insert()
        return doc
    doc.employee_profile_linked = True
    if department_id:
        doc.department_id = department_id
    if campus_id:
        doc.campus_id = campus_id
    doc.updated_at = utcnow()
    await doc.save()
    return doc


async def register_employee(scope: AccessScope, payload: EmployeeRegister) -> EmployeeProfileRead:
    authorize_hr_employee_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    code = payload.employee_code.strip()
    if await HrEmployeeProfile.find_one(Eq(HrEmployeeProfile.tenant_id, tenant_id), Eq(HrEmployeeProfile.employee_code, code)):
        raise AppError(code="CONFLICT", message="Employee code already exists", status_code=409)
    dept_id = to_object_id(payload.department_id, "department_id")
    await _validate_department(tenant_id, dept_id)
    campus_id = to_object_id(payload.campus_id, "campus_id") if payload.campus_id else None
    await _validate_campus(tenant_id, campus_id)
    manager_id = to_object_id(payload.reporting_manager_user_id, "reporting_manager_user_id") if payload.reporting_manager_user_id else None
    await _validate_manager(tenant_id, manager_id)

    official_email = str(payload.official_email).lower()
    if not _EMAIL_RE.match(official_email):
        raise AppError(code="VALIDATION_ERROR", message="Invalid official email", status_code=422)

    if payload.institution_role not in _EMPLOYEE_CREATABLE_ROLES and payload.link_existing_user_id is None:
        raise AppError(code="VALIDATION_ERROR", message="Unsupported institution role for HR registration", status_code=422)

    user: User
    if payload.link_existing_user_id:
        user_id = to_object_id(payload.link_existing_user_id, "link_existing_user_id")
        user = await _user_repo.get(user_id)
        if user is None or user.tenant_id != tenant_id:
            raise AppError(code="NOT_FOUND", message="User not found in this college", status_code=404)
        faculty = await FacultyRecord.find_one(Eq(FacultyRecord.tenant_id, tenant_id), Eq(FacultyRecord.user_id, user_id))
        if faculty and user.role == Role.FACULTY:
            existing_profile = await HrEmployeeProfile.find_one(Eq(HrEmployeeProfile.tenant_id, tenant_id), Eq(HrEmployeeProfile.user_id, user_id))
            if existing_profile:
                raise AppError(code="CONFLICT", message="HR profile already exists for this faculty member", status_code=409)
    else:
        if not payload.password:
            raise AppError(code="VALIDATION_ERROR", message="Password is required for new users", status_code=422)
        if await _user_repo.find_by_email_in_tenant(official_email, tenant_id):
            raise AppError(code="CONFLICT", message="Official email already exists", status_code=409)
        user = User(
            email=official_email,
            hashed_password=hash_password(payload.password),
            full_name=f"{payload.first_name} {payload.last_name}".strip(),
            role=payload.institution_role,
            tenant_id=tenant_id,
            department_id=dept_id,
        )
        await user.insert()

    employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, user.id))
    if employee is None:
        if await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.employee_id, code)):
            raise AppError(code="CONFLICT", message="Employee identifier already assigned", status_code=409)
        employee = EmployeeRecord(
            tenant_id=tenant_id,
            user_id=user.id,
            employee_id=code,
            employment_type=payload.employment_type,
            joining_date=payload.joining_date,
            designation=payload.designation,
            department_id=dept_id,
            campus_id=campus_id,
            employment_status=payload.employment_status,
            is_faculty=user.role == Role.FACULTY,
            updated_by=scope.user_id,
        )
        await employee.insert()
    else:
        employee.employee_id = employee.employee_id or code
        employee.employment_type = payload.employment_type
        employee.joining_date = payload.joining_date
        employee.designation = payload.designation
        employee.department_id = dept_id
        employee.campus_id = campus_id
        employee.employment_status = payload.employment_status
        employee.updated_by = scope.user_id
        employee.updated_at = utcnow()
        await employee.save()

    profile = HrEmployeeProfile(
        tenant_id=tenant_id,
        user_id=user.id,
        employee_record_id=employee.id,
        employee_code=code,
        first_name=payload.first_name.strip(),
        middle_name=(payload.middle_name.strip() if payload.middle_name else None),
        last_name=payload.last_name.strip(),
        official_email=official_email,
        personal_email=payload.personal_email,
        mobile_number=payload.mobile_number.strip(),
        alternate_contact_number=payload.alternate_contact_number,
        date_of_birth=payload.date_of_birth,
        gender=payload.gender,
        marital_status=payload.marital_status,
        nationality=payload.nationality,
        profile_photo_file_id=payload.profile_photo_file_id,
        current_address=payload.current_address,
        permanent_address=payload.permanent_address or (payload.current_address if payload.addresses_same else None),
        addresses_same=payload.addresses_same,
        emergency_contact=payload.emergency_contact,
        employee_category=payload.employee_category,
        reporting_manager_user_id=manager_id,
        probation_start_date=payload.probation_start_date or payload.joining_date,
        probation_end_date=payload.probation_end_date,
        contract_end_date=payload.contract_end_date,
        profile_verification_status=ProfileVerificationStatus.PENDING_VERIFICATION,
        updated_by=scope.user_id,
    )
    apply_completion_status(profile, employee)
    await profile.insert()
    await _ensure_institution_user(tenant_id, user.id, department_id=dept_id, campus_id=campus_id)
    await ensure_current_assignment(tenant_id, employee, profile, actor_id=scope.user_id)
    await sync_employee_snapshot(employee)
    await FacultyEmploymentHistory(
        tenant_id=tenant_id,
        user_id=user.id,
        event_type="hr_registered",
        to_status=employee.employment_status.value,
        effective_date=payload.joining_date,
        actor_id=scope.user_id,
        note="Employee registered via HR staff portal",
    ).insert()
    await log_hr_activity(
        tenant_id,
        HrStaffActivityType.EMPLOYEE_REGISTERED,
        f"Employee {code} registered",
        actor_id=scope.user_id,
        employee_user_id=user.id,
        department_id=dept_id,
        campus_id=campus_id,
        resource_type="hr_employee_profile",
        resource_id=str(profile.id),
        status_label=employee.employment_status.value,
    )
    return EmployeeProfileRead.from_parts(profile, employee)


async def get_employee_profile(scope: AccessScope, profile_id: str) -> EmployeeProfileRead:
    authorize_hr_employee_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    pid = to_object_id(profile_id, "profile_id")
    profile = await HrEmployeeProfile.get(pid)
    if profile is None or profile.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Employee profile not found", status_code=404)
    employee = await EmployeeRecord.get(profile.employee_record_id)
    if employee is None:
        raise AppError(code="NOT_FOUND", message="Employee record not found", status_code=404)
    return EmployeeProfileRead.from_parts(profile, employee)


async def update_employee_profile(scope: AccessScope, profile_id: str, payload: EmployeeProfileUpdate) -> EmployeeProfileRead:
    authorize_hr_employee_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    pid = to_object_id(profile_id, "profile_id")
    profile = await HrEmployeeProfile.get(pid)
    if profile is None or profile.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Employee profile not found", status_code=404)
    employee = await EmployeeRecord.get(profile.employee_record_id)
    if employee is None:
        raise AppError(code="NOT_FOUND", message="Employee record not found", status_code=404)

    data = payload.model_dump(exclude_none=True)
    reason = data.pop("change_reason", None)
    profile_changes: dict = {}
    employee_changes: dict = {}
    prev_profile: dict = {}
    prev_employee: dict = {}

    for key, value in list(data.items()):
        if key in {"department_id", "designation", "employment_type", "campus_id"}:
            employee_changes[key] = value
        elif hasattr(profile, key):
            profile_changes[key] = value

    if "department_id" in employee_changes:
        dept_id = to_object_id(employee_changes["department_id"], "department_id")
        await _validate_department(tenant_id, dept_id)
        prev_employee["department_id"] = str(employee.department_id) if employee.department_id else None
        employee.department_id = dept_id
    if "campus_id" in employee_changes:
        campus_id = to_object_id(employee_changes["campus_id"], "campus_id")
        await _validate_campus(tenant_id, campus_id)
        prev_employee["campus_id"] = str(employee.campus_id) if employee.campus_id else None
        employee.campus_id = campus_id
    if "designation" in employee_changes:
        prev_employee["designation"] = employee.designation
        employee.designation = employee_changes["designation"]
    if "employment_type" in employee_changes:
        prev_employee["employment_type"] = employee.employment_type
        employee.employment_type = employee_changes["employment_type"]

    if "reporting_manager_user_id" in profile_changes:
        manager_id = to_object_id(profile_changes["reporting_manager_user_id"], "reporting_manager_user_id")
        await _validate_manager(tenant_id, manager_id)
        prev_profile["reporting_manager_user_id"] = str(profile.reporting_manager_user_id) if profile.reporting_manager_user_id else None
        profile.reporting_manager_user_id = manager_id
        profile_changes.pop("reporting_manager_user_id", None)

    for key, value in profile_changes.items():
        prev_profile[key] = getattr(profile, key)
        if key == "mobile_number" and value:
            value = str(value).strip()
        setattr(profile, key, value)

    if profile_changes or employee_changes:
        if not reason and any(k in profile_changes for k in ("date_of_birth", "gender", "nationality")):
            raise AppError(code="VALIDATION_ERROR", message="Reason required for sensitive profile changes", status_code=422)

    profile.updated_by = scope.user_id
    profile.updated_at = utcnow()
    employee.updated_by = scope.user_id
    employee.updated_at = utcnow()
    apply_completion_status(profile, employee)
    if profile.profile_verification_status == ProfileVerificationStatus.VERIFIED and profile_changes:
        profile.profile_verification_status = ProfileVerificationStatus.PENDING_VERIFICATION

    await profile.save()
    await employee.save()
    await sync_employee_snapshot(employee)

    if profile_changes:
        await HrEmployeeProfileChangeLog(
            tenant_id=tenant_id,
            user_id=profile.user_id,
            field_group="personal",
            changes=profile_changes,
            previous_values=prev_profile,
            reason=reason,
            actor_id=scope.user_id,
        ).insert()
    if employee_changes:
        await HrEmployeeProfileChangeLog(
            tenant_id=tenant_id,
            user_id=profile.user_id,
            field_group="employment",
            changes=employee_changes,
            previous_values=prev_employee,
            reason=reason,
            actor_id=scope.user_id,
        ).insert()
        event = HrStaffActivityType.DEPARTMENT_CHANGED if "department_id" in employee_changes else HrStaffActivityType.PROFILE_UPDATED
        if "designation" in employee_changes:
            event = HrStaffActivityType.DESIGNATION_CHANGED
        await log_hr_activity(
            tenant_id,
            event,
            f"Employee {profile.employee_code} profile updated",
            actor_id=scope.user_id,
            employee_user_id=profile.user_id,
            department_id=employee.department_id,
            campus_id=employee.campus_id,
            resource_type="hr_employee_profile",
            resource_id=str(profile.id),
        )
    return EmployeeProfileRead.from_parts(profile, employee)


async def search_employees(scope: AccessScope, query: EmployeeSearchQuery, pagination: Pagination) -> Page[EmployeeListItem]:
    authorize_hr_employee_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    match: dict = {"tenant_id": tenant_id}
    if query.profile_completion_status:
        match["profile_completion_status"] = query.profile_completion_status.value
    if query.profile_verification_status:
        match["profile_verification_status"] = query.profile_verification_status.value
    if query.employee_code:
        match["employee_code"] = query.employee_code.strip()
    if query.official_email:
        match["official_email"] = query.official_email.lower()
    if query.mobile_number:
        match["mobile_number"] = query.mobile_number.strip()
    if query.name:
        token = query.name.strip().lower()
        match["$or"] = [
            {"first_name": {"$regex": token, "$options": "i"}},
            {"last_name": {"$regex": token, "$options": "i"}},
            {"employee_code": {"$regex": token, "$options": "i"}},
        ]

    profiles = await HrEmployeeProfile.find(match).sort("-created_at").to_list()
    items: list[EmployeeListItem] = []
    for profile in profiles:
        employee = await EmployeeRecord.get(profile.employee_record_id)
        if employee is None:
            continue
        if query.department_id and str(employee.department_id) != query.department_id:
            continue
        if query.campus_id and str(employee.campus_id) != query.campus_id:
            continue
        if query.designation and (employee.designation or "").lower() != query.designation.lower():
            continue
        if query.employment_type and (employee.employment_type or "").lower() != query.employment_type.lower():
            continue
        if query.employment_status and employee.employment_status != query.employment_status:
            continue
        if query.joining_from and (not employee.joining_date or employee.joining_date < query.joining_from):
            continue
        if query.joining_to and (not employee.joining_date or employee.joining_date > query.joining_to):
            continue
        if query.probation_only and employee.employment_status != FacultyEmploymentStatus.PROBATION:
            continue
        items.append(
            EmployeeListItem(
                profile_id=str(profile.id),
                user_id=str(profile.user_id),
                employee_code=profile.employee_code,
                full_name=f"{profile.first_name} {profile.last_name}".strip(),
                official_email=str(profile.official_email),
                department_id=str(employee.department_id) if employee.department_id else None,
                designation=employee.designation,
                employment_status=employee.employment_status,
                profile_completion_status=profile.profile_completion_status,
                profile_verification_status=profile.profile_verification_status,
            )
        )
    total = len(items)
    page_items = items[pagination.offset : pagination.offset + pagination.limit]
    return Page(items=page_items, total=total, limit=pagination.limit, offset=pagination.offset)


async def decide_profile_verification(
    scope: AccessScope, profile_id: str, payload: ProfileVerificationDecision
) -> EmployeeProfileRead:
    authorize(scope, Permission.HR_EMPLOYEE_VERIFY)
    tenant_id = require_hr_tenant_scope(scope)
    if payload.decision not in {ProfileVerificationStatus.VERIFIED, ProfileVerificationStatus.REJECTED}:
        raise AppError(code="VALIDATION_ERROR", message="Invalid verification decision", status_code=422)
    pid = to_object_id(profile_id, "profile_id")
    profile = await HrEmployeeProfile.get(pid)
    if profile is None or profile.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Employee profile not found", status_code=404)
    employee = await EmployeeRecord.get(profile.employee_record_id)
    if employee is None:
        raise AppError(code="NOT_FOUND", message="Employee record not found", status_code=404)
    if payload.decision == ProfileVerificationStatus.VERIFIED and profile.profile_completion_status.value != "complete":
        raise AppError(code="VALIDATION_ERROR", message="Cannot verify an incomplete profile", status_code=422)
    profile.profile_verification_status = payload.decision
    profile.verification_note = payload.note
    profile.verified_by = scope.user_id
    profile.verified_at = utcnow()
    profile.updated_at = utcnow()
    await profile.save()
    await log_hr_activity(
        tenant_id,
        HrStaffActivityType.PROFILE_VERIFICATION,
        f"Profile verification {payload.decision.value} for {profile.employee_code}",
        actor_id=scope.user_id,
        employee_user_id=profile.user_id,
        department_id=employee.department_id,
        status_label=payload.decision.value,
        resource_type="hr_employee_profile",
        resource_id=str(profile.id),
    )
    return EmployeeProfileRead.from_parts(profile, employee)


async def change_employment_status(scope: AccessScope, profile_id: str, payload: EmploymentStatusChange) -> EmployeeProfileRead:
    authorize_hr_employee_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    pid = to_object_id(profile_id, "profile_id")
    profile = await HrEmployeeProfile.get(pid)
    if profile is None or profile.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Employee profile not found", status_code=404)
    employee = await EmployeeRecord.get(profile.employee_record_id)
    if employee is None:
        raise AppError(code="NOT_FOUND", message="Employee record not found", status_code=404)
    new_status = payload.new_status
    if new_status.value in OFFBOARDING_REQUIRED_STATUSES:
        offboarding = await EmployeeOffboardingRecord.find_one(
            Eq(EmployeeOffboardingRecord.tenant_id, tenant_id),
            Eq(EmployeeOffboardingRecord.user_id, profile.user_id),
        )
        if offboarding is None:
            raise AppError(
                code="WORKFLOW_REQUIRED",
                message="Resignation and termination require an offboarding record",
                status_code=422,
            )
    previous = employee.employment_status
    if previous == new_status:
        raise AppError(code="VALIDATION_ERROR", message="Employee is already in this status", status_code=422)
    employee.employment_status = new_status
    employee.updated_by = scope.user_id
    employee.updated_at = utcnow()
    if new_status == FacultyEmploymentStatus.CONFIRMED and not profile.confirmation_date:
        profile.confirmation_date = payload.effective_date or utcnow().date()
        profile.updated_at = utcnow()
        await profile.save()
    await employee.save()
    await sync_employee_snapshot(employee)
    await FacultyEmploymentHistory(
        tenant_id=tenant_id,
        user_id=profile.user_id,
        event_type="status_change",
        from_status=previous.value,
        to_status=new_status.value,
        effective_date=payload.effective_date,
        actor_id=scope.user_id,
        note=payload.reason,
    ).insert()
    if new_status in {FacultyEmploymentStatus.INACTIVE, FacultyEmploymentStatus.RESIGNED, FacultyEmploymentStatus.TERMINATED}:
        inst = await InstitutionUser.find_one(Eq(InstitutionUser.tenant_id, tenant_id), Eq(InstitutionUser.user_id, profile.user_id))
        if inst and new_status != FacultyEmploymentStatus.ACTIVE:
            inst.account_status = InstitutionAccountStatus.DEACTIVATED
            inst.updated_at = utcnow()
            await inst.save()
    await log_hr_activity(
        tenant_id,
        HrStaffActivityType.STATUS_CHANGED if new_status.value not in OFFBOARDING_REQUIRED_STATUSES else HrStaffActivityType.EMPLOYEE_EXIT,
        f"Employment status changed to {new_status.value}",
        actor_id=scope.user_id,
        employee_user_id=profile.user_id,
        department_id=employee.department_id,
        status_label=new_status.value,
        resource_type="employee_record",
        resource_id=str(employee.id),
    )
    return EmployeeProfileRead.from_parts(profile, employee)


async def submit_profile_correction(scope: AccessScope, user: User, payload: ProfileCorrectionSubmit) -> ProfileCorrectionRead:
    authorize(scope, Permission.HR_SELF_ACCESS)
    tenant_id = require_hr_tenant_scope(scope)
    if user.tenant_id != tenant_id:
        raise AppError(code="FORBIDDEN", message="College context mismatch", status_code=403)
    profile = await HrEmployeeProfile.find_one(Eq(HrEmployeeProfile.tenant_id, tenant_id), Eq(HrEmployeeProfile.user_id, user.id))
    if profile is None:
        raise AppError(code="NOT_FOUND", message="Employee profile not found", status_code=404)
    allowed = frozenset({"personal_email", "mobile_number", "alternate_contact_number", "current_address", "permanent_address", "emergency_contact"})
    proposed = {k: v for k, v in payload.proposed_changes.items() if k in allowed}
    if not proposed:
        raise AppError(code="VALIDATION_ERROR", message="No permitted correction fields submitted", status_code=422)
    pending = await HrEmployeeProfileCorrectionRequest.find_one(
        Eq(HrEmployeeProfileCorrectionRequest.tenant_id, tenant_id),
        Eq(HrEmployeeProfileCorrectionRequest.employee_user_id, user.id),
        Eq(HrEmployeeProfileCorrectionRequest.status, ProfileCorrectionStatus.SUBMITTED),
    )
    if pending:
        raise AppError(code="CONFLICT", message="A correction request is already pending", status_code=409)
    snapshot = {
        "personal_email": str(profile.personal_email) if profile.personal_email else None,
        "mobile_number": profile.mobile_number,
        "alternate_contact_number": profile.alternate_contact_number,
        "current_address": profile.current_address.model_dump() if profile.current_address else None,
        "permanent_address": profile.permanent_address.model_dump() if profile.permanent_address else None,
        "emergency_contact": profile.emergency_contact.model_dump() if profile.emergency_contact else None,
    }
    row = HrEmployeeProfileCorrectionRequest(
        tenant_id=tenant_id,
        employee_user_id=user.id,
        proposed_changes=proposed,
        current_snapshot=snapshot,
        employee_note=payload.employee_note,
    )
    await row.insert()
    await log_hr_activity(
        tenant_id,
        HrStaffActivityType.PROFILE_CORRECTION,
        "Employee submitted a profile correction request",
        actor_id=user.id,
        employee_user_id=user.id,
        resource_type="hr_profile_correction",
        resource_id=str(row.id),
        status_label=ProfileCorrectionStatus.SUBMITTED.value,
    )
    return ProfileCorrectionRead(
        correction_id=str(row.id),
        employee_user_id=str(row.employee_user_id),
        proposed_changes=row.proposed_changes,
        current_snapshot=row.current_snapshot,
        employee_note=row.employee_note,
        status=row.status,
        reviewer_note=row.reviewer_note,
        created_at=row.created_at,
        resolved_at=row.resolved_at,
    )


async def review_profile_correction(scope: AccessScope, correction_id: str, payload: ProfileCorrectionReview) -> ProfileCorrectionRead:
    authorize(scope, Permission.HR_PROFILE_CORRECTION_REVIEW)
    tenant_id = require_hr_tenant_scope(scope)
    if payload.decision not in {ProfileCorrectionStatus.APPROVED, ProfileCorrectionStatus.REJECTED}:
        raise AppError(code="VALIDATION_ERROR", message="Invalid correction decision", status_code=422)
    cid = to_object_id(correction_id, "correction_id")
    row = await HrEmployeeProfileCorrectionRequest.get(cid)
    if row is None or row.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Correction request not found", status_code=404)
    if row.status != ProfileCorrectionStatus.SUBMITTED:
        raise AppError(code="CONFLICT", message="Correction request is not pending", status_code=409)
    profile = await HrEmployeeProfile.find_one(Eq(HrEmployeeProfile.tenant_id, tenant_id), Eq(HrEmployeeProfile.user_id, row.employee_user_id))
    if profile is None:
        raise AppError(code="NOT_FOUND", message="Employee profile not found", status_code=404)
    employee = await EmployeeRecord.get(profile.employee_record_id)
    if employee is None:
        raise AppError(code="NOT_FOUND", message="Employee record not found", status_code=404)

    row.status = payload.decision
    row.reviewer_id = scope.user_id
    row.reviewer_note = payload.reviewer_note
    row.resolved_at = utcnow()
    row.updated_at = utcnow()

    if payload.decision == ProfileCorrectionStatus.APPROVED:
        for key, value in row.proposed_changes.items():
            setattr(profile, key, value)
        profile.updated_at = utcnow()
        profile.profile_verification_status = ProfileVerificationStatus.PENDING_VERIFICATION
        apply_completion_status(profile, employee)
        await profile.save()
        await sync_employee_snapshot(employee)

    await row.save()
    await log_hr_activity(
        tenant_id,
        HrStaffActivityType.PROFILE_CORRECTION,
        f"Profile correction {payload.decision.value}",
        actor_id=scope.user_id,
        employee_user_id=row.employee_user_id,
        resource_type="hr_profile_correction",
        resource_id=str(row.id),
        status_label=payload.decision.value,
    )
    return ProfileCorrectionRead(
        correction_id=str(row.id),
        employee_user_id=str(row.employee_user_id),
        proposed_changes=row.proposed_changes,
        current_snapshot=row.current_snapshot,
        employee_note=row.employee_note,
        status=row.status,
        reviewer_note=row.reviewer_note,
        created_at=row.created_at,
        resolved_at=row.resolved_at,
    )


async def list_pending_corrections(scope: AccessScope, pagination: Pagination) -> Page[ProfileCorrectionRead]:
    authorize(scope, Permission.HR_PROFILE_CORRECTION_REVIEW)
    tenant_id = require_hr_tenant_scope(scope)
    query = HrEmployeeProfileCorrectionRequest.find(
        Eq(HrEmployeeProfileCorrectionRequest.tenant_id, tenant_id),
        Eq(HrEmployeeProfileCorrectionRequest.status, ProfileCorrectionStatus.SUBMITTED),
    )
    total = await query.count()
    rows = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    items = [
        ProfileCorrectionRead(
            correction_id=str(r.id),
            employee_user_id=str(r.employee_user_id),
            proposed_changes=r.proposed_changes,
            current_snapshot=r.current_snapshot,
            employee_note=r.employee_note,
            status=r.status,
            reviewer_note=r.reviewer_note,
            created_at=r.created_at,
            resolved_at=r.resolved_at,
        )
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def profile_change_history(scope: AccessScope, profile_id: str, pagination: Pagination) -> Page[ProfileChangeHistoryItem]:
    authorize_hr_employee_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    pid = to_object_id(profile_id, "profile_id")
    profile = await HrEmployeeProfile.get(pid)
    if profile is None or profile.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Employee profile not found", status_code=404)
    query = HrEmployeeProfileChangeLog.find(
        Eq(HrEmployeeProfileChangeLog.tenant_id, tenant_id),
        Eq(HrEmployeeProfileChangeLog.user_id, profile.user_id),
    )
    total = await query.count()
    rows = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    items = [
        ProfileChangeHistoryItem(
            field_group=r.field_group,
            changes=r.changes,
            previous_values=r.previous_values,
            reason=r.reason,
            actor_id=str(r.actor_id) if r.actor_id else None,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)