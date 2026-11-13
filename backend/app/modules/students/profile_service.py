"""Student profile (permitted self-service updates)."""

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.students.enums import StudentActivityType
from app.modules.students.models import StudentProfile
from app.modules.students.policy import require_student_scope
from app.modules.students.repositories import StudentActivityRepository, StudentProfileRepository
from app.modules.students.schemas import StudentActivityRead, StudentProfileRead, StudentProfileUpdate
from app.modules.tenants.models import Department

_profile_repo = StudentProfileRepository()
_activity_repo = StudentActivityRepository()

_UPDATABLE_FIELDS = frozenset(
    {
        "contact_phone",
        "alternate_email",
        "permanent_address",
        "current_address",
        "emergency_contacts",
        "bio",
        "profile_photo_ref",
    }
)


async def _department_name(tenant_id: PydanticObjectId, department_id: PydanticObjectId | None) -> str | None:
    if department_id is None:
        return None
    department = await Department.get(department_id)
    if department is None or str(department.tenant_id) != str(tenant_id):
        return None
    return department.name


async def ensure_student_profile(scope: AccessScope, user: User) -> StudentProfile:
    tenant_id = require_student_scope(scope)
    if user.tenant_id is None or str(user.tenant_id) != str(tenant_id):
        raise AppError(code="FORBIDDEN", message="User does not belong to this college", status_code=403)
    existing = await _profile_repo.get_by_user(tenant_id, user.id)
    if existing is not None:
        return existing
    profile = StudentProfile(
        tenant_id=tenant_id,
        user_id=user.id,
        department_id=user.department_id,
    )
    await profile.insert()
    await _activity_repo.append(
        tenant_id=tenant_id,
        user_id=user.id,
        activity_type=StudentActivityType.OTHER,
        title="Student workspace initialized",
        description="Profile record created on first access",
    )
    return profile


async def get_student_profile(scope: AccessScope, user: User) -> StudentProfileRead:
    authorize(scope, Permission.STUDENT_PROFILE_READ)
    profile = await ensure_student_profile(scope, user)
    department_name = await _department_name(profile.tenant_id, profile.department_id)
    return StudentProfileRead.from_parts(
        profile,
        full_name=user.full_name,
        email=user.email,
        department_name=department_name,
    )


async def update_student_profile(scope: AccessScope, user: User, payload: StudentProfileUpdate) -> StudentProfileRead:
    authorize(scope, Permission.STUDENT_PROFILE_UPDATE)
    profile = await ensure_student_profile(scope, user)
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
        return StudentProfileRead.from_parts(
            profile,
            full_name=user.full_name,
            email=user.email,
            department_name=department_name,
        )
    profile.updated_at = utcnow()
    await profile.save()
    await record_audit(
        actor_id=scope.user_id,
        action="student.profile.updated",
        resource_type="student_profile",
        resource_id=str(profile.id),
        tenant_id=tenant_id,
        metadata={"fields": list(changes.keys())},
    )
    await _activity_repo.append(
        tenant_id=tenant_id,
        user_id=user.id,
        activity_type=StudentActivityType.PROFILE_UPDATED,
        title="Profile updated",
        description=f"Updated fields: {', '.join(changes.keys())}",
    )
    department_name = await _department_name(tenant_id, profile.department_id)
    return StudentProfileRead.from_parts(
        profile,
        full_name=user.full_name,
        email=user.email,
        department_name=department_name,
    )


async def get_profile_activity_history(
    scope: AccessScope, user: User, pagination: Pagination
) -> Page[StudentActivityRead]:
    authorize(scope, Permission.STUDENT_PROFILE_READ)
    tenant_id = require_student_scope(scope)
    skip = (pagination.page - 1) * pagination.page_size
    items, total = await _activity_repo.page_for_user(tenant_id, user.id, skip=skip, limit=pagination.page_size)
    return Page(
        items=[StudentActivityRead.from_document(row) for row in items],
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )
