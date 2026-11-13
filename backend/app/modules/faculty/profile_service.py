"""Faculty profile and teaching responsibilities."""

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.faculty.enums import FacultyActivityType
from app.modules.faculty.models import FacultyProfile
from app.modules.faculty.policy import require_faculty_scope
from app.modules.faculty.repositories import (
    FacultyActivityRepository,
    FacultyAssignmentRepository,
    FacultyProfileRepository,
    FacultyWorkloadRepository,
)
from app.modules.faculty.schemas import (
    FacultyActivityRead,
    FacultyProfileRead,
    FacultyProfileUpdate,
    TeachingResponsibilityRead,
    WorkloadDetailRead,
)
from app.modules.tenants.models import Department

_profile_repo = FacultyProfileRepository()
_assignment_repo = FacultyAssignmentRepository()
_workload_repo = FacultyWorkloadRepository()
_activity_repo = FacultyActivityRepository()

_UPDATABLE_FIELDS = frozenset({"contact_phone", "office_location", "bio", "document_refs"})


async def _department_name(tenant_id: PydanticObjectId, department_id: PydanticObjectId | None) -> str | None:
    if department_id is None:
        return None
    department = await Department.get(department_id)
    if department is None or str(department.tenant_id) != str(tenant_id):
        return None
    return department.name


async def ensure_faculty_profile(scope: AccessScope, user: User) -> FacultyProfile:
    tenant_id = require_faculty_scope(scope)
    if user.tenant_id is None or str(user.tenant_id) != str(tenant_id):
        raise AppError(code="FORBIDDEN", message="User does not belong to this college", status_code=403)
    existing = await _profile_repo.get_by_user(tenant_id, user.id)
    if existing is not None:
        return existing
    profile = FacultyProfile(
        tenant_id=tenant_id,
        user_id=user.id,
        department_id=user.department_id,
        designation="Faculty",
    )
    await profile.insert()
    await _activity_repo.append(
        tenant_id=tenant_id,
        user_id=user.id,
        activity_type=FacultyActivityType.OTHER,
        title="Faculty workspace initialized",
        description="Profile record created on first access",
    )
    return profile


async def get_faculty_profile(scope: AccessScope, user: User) -> FacultyProfileRead:
    authorize(scope, Permission.FACULTY_PROFILE_READ)
    profile = await ensure_faculty_profile(scope, user)
    tenant_id = profile.tenant_id
    department_name = await _department_name(tenant_id, profile.department_id)
    return FacultyProfileRead.from_parts(
        profile,
        full_name=user.full_name,
        email=user.email,
        department_name=department_name,
    )


async def update_faculty_profile(scope: AccessScope, user: User, payload: FacultyProfileUpdate) -> FacultyProfileRead:
    authorize(scope, Permission.FACULTY_PROFILE_UPDATE)
    profile = await ensure_faculty_profile(scope, user)
    tenant_id = profile.tenant_id
    changes: dict[str, object] = {}
    for field in _UPDATABLE_FIELDS:
        value = getattr(payload, field)
        if value is None:
            continue
        if getattr(profile, field) != value:
            changes[field] = value
            setattr(profile, field, value)
    if not changes:
        department_name = await _department_name(tenant_id, profile.department_id)
        return FacultyProfileRead.from_parts(
            profile,
            full_name=user.full_name,
            email=user.email,
            department_name=department_name,
        )
    profile.updated_at = utcnow()
    await profile.save()
    await _activity_repo.append(
        tenant_id=tenant_id,
        user_id=user.id,
        activity_type=FacultyActivityType.PROFILE_UPDATED,
        title="Profile updated",
        metadata={"fields": list(changes.keys())},
    )
    await record_audit(
        actor_id=scope.user_id,
        action="faculty.profile.updated",
        resource_type="faculty_profile",
        resource_id=str(profile.id),
        tenant_id=tenant_id,
        metadata={"fields": list(changes.keys())},
    )
    department_name = await _department_name(tenant_id, profile.department_id)
    return FacultyProfileRead.from_parts(
        profile,
        full_name=user.full_name,
        email=user.email,
        department_name=department_name,
    )


async def get_teaching_responsibilities(scope: AccessScope, user: User) -> list[TeachingResponsibilityRead]:
    authorize(scope, Permission.FACULTY_TEACHING_READ)
    tenant_id = require_faculty_scope(scope)
    assignments = await _assignment_repo.list_active_for_user(tenant_id, user.id)
    return [TeachingResponsibilityRead.from_document(item) for item in assignments]


async def get_assigned_courses(scope: AccessScope, user: User) -> list[TeachingResponsibilityRead]:
    return await get_teaching_responsibilities(scope, user)


async def get_workload_summary(scope: AccessScope, user: User) -> WorkloadDetailRead:
    tenant_id = require_faculty_scope(scope)
    from app.modules.faculty.integrations.academic_reader import AcademicDataReader

    context = await AcademicDataReader().current_academic_context(tenant_id)
    year = context.academic_year_label if context else ""
    semester = context.semester_label if context else ""
    workload = None
    if year and semester:
        document = await _workload_repo.get_for_term(tenant_id, user.id, year, semester)
        if document is not None:
            workload = WorkloadDetailRead.workload_from_document(document)
    assignments = await _assignment_repo.list_active_for_user(
        tenant_id,
        user.id,
        academic_year_label=year or None,
        semester_label=semester or None,
    )
    return WorkloadDetailRead(
        workload=workload,
        assignments=[TeachingResponsibilityRead.from_document(item) for item in assignments],
    )


async def get_profile_activity_history(
    scope: AccessScope,
    user: User,
    pagination: Pagination,
) -> Page[FacultyActivityRead]:
    tenant_id = require_faculty_scope(scope)
    items, total = await _activity_repo.list_for_user(
        tenant_id,
        user.id,
        skip=pagination.offset,
        limit=pagination.limit,
    )
    return Page(
        items=[FacultyActivityRead.from_document(item) for item in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def get_assignment_history(
    scope: AccessScope,
    user: User,
    pagination: Pagination,
) -> Page[TeachingResponsibilityRead]:
    tenant_id = require_faculty_scope(scope)
    items, total = await _assignment_repo.list_history_for_user(
        tenant_id,
        user.id,
        skip=pagination.offset,
        limit=pagination.limit,
    )
    return Page(
        items=[TeachingResponsibilityRead.from_document(item) for item in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )
