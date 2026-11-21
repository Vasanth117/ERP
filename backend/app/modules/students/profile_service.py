"""Student profile (permitted self-service updates)."""

from datetime import date

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

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
from app.modules.college_admin.student_admin_models import StudentAdmission, StudentGuardianRelationship
from app.modules.students.schemas import (
    GuardianContactRead,
    StudentActivityRead,
    StudentOfficialPersonalRead,
    StudentProfileRead,
    StudentProfileUpdate,
)
from app.modules.tenants.models import Department

_profile_repo = StudentProfileRepository()
_activity_repo = StudentActivityRepository()

_UPDATABLE_FIELDS = frozenset(
    {
        "contact_phone",
        "alternate_contact_phone",
        "alternate_email",
        "permanent_address",
        "current_address",
        "emergency_contacts",
        "bio",
        "profile_photo_ref",
    }
)


def _meta_str(metadata: dict, *keys: str) -> str | None:
    for key in keys:
        value = metadata.get(key)
        if value is None or value == "":
            continue
        return str(value)
    return None


def _meta_date(metadata: dict, *keys: str) -> date | None:
    raw = _meta_str(metadata, *keys)
    if raw is None:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _mask_aadhaar(raw: str | None) -> str | None:
    if not raw:
        return None
    digits = "".join(c for c in raw if c.isdigit())
    if len(digits) < 4:
        return "XXXX XXXX ****"
    tail = digits[-4:]
    return f"XXXX XXXX {tail}"


def _title_gender(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.replace("_", " ").strip()
    if normalized.lower() in {"male", "female", "other"}:
        return normalized.capitalize()
    return normalized.title()


async def _load_admission(tenant_id: PydanticObjectId, user_id: PydanticObjectId, profile: StudentProfile) -> StudentAdmission | None:
    admission = await StudentAdmission.find_one(
        Eq(StudentAdmission.tenant_id, tenant_id),
        Eq(StudentAdmission.confirmed_user_id, user_id),
    )
    if admission is not None:
        return admission
    if profile.admission_number:
        return await StudentAdmission.find_one(
            Eq(StudentAdmission.tenant_id, tenant_id),
            Eq(StudentAdmission.admission_number, profile.admission_number),
        )
    return None


async def _official_personal(
    profile: StudentProfile,
    *,
    admission: StudentAdmission | None,
) -> StudentOfficialPersonalRead:
    meta = admission.metadata if admission else {}
    religion = _meta_str(meta, "religion")
    community = _meta_str(meta, "community", "caste", "category")
    identity_verified = bool(
        any(doc.authorized for doc in profile.document_refs)
        or meta.get("identity_verified") is True
    )
    return StudentOfficialPersonalRead(
        gender=_title_gender(_meta_str(meta, "gender", "sex")),
        date_of_birth=_meta_date(meta, "date_of_birth", "dob"),
        nationality=_meta_str(meta, "nationality"),
        mother_tongue=_meta_str(meta, "mother_tongue", "mother_tongue_name"),
        blood_group=_meta_str(meta, "blood_group"),
        religion=religion,
        community=community,
        aadhaar_masked=_mask_aadhaar(_meta_str(meta, "aadhaar", "aadhaar_number")),
        alternate_mobile=profile.alternate_contact_phone or _meta_str(meta, "alternate_mobile", "alternate_phone"),
        personal_email=profile.alternate_email,
        identity_documents_verified=identity_verified,
    )


async def _guardian_contacts(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> list[GuardianContactRead]:
    rows = await StudentGuardianRelationship.find(
        Eq(StudentGuardianRelationship.tenant_id, tenant_id),
        Eq(StudentGuardianRelationship.user_id, user_id),
    ).sort("relationship").to_list()
    return [
        GuardianContactRead(
            name=row.guardian_name,
            relationship=row.relationship,
            phone=row.phone,
            email=row.email,
            occupation=row.occupation,
        )
        for row in rows
    ]


def _official_full_name(user: User, admission: StudentAdmission | None) -> str:
    if admission is not None and admission.applicant_name and admission.applicant_name.strip():
        return admission.applicant_name.strip()
    return user.full_name


async def _enriched_profile_read(
    profile: StudentProfile,
    *,
    user: User,
    email: str,
    department_name: str | None,
) -> StudentProfileRead:
    admission = await _load_admission(profile.tenant_id, profile.user_id, profile)
    full_name = _official_full_name(user, admission)
    official = await _official_personal(profile, admission=admission)
    guardians = await _guardian_contacts(profile.tenant_id, profile.user_id)
    return StudentProfileRead.from_parts(
        profile,
        full_name=full_name,
        email=email,
        department_name=department_name,
        official_personal=official,
        guardians=guardians,
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
    return await _enriched_profile_read(
        profile,
        user=user,
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
        return await _enriched_profile_read(
            profile,
            user=user,
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
    return await _enriched_profile_read(
        profile,
        user=user,
        email=user.email,
        department_name=department_name,
    )


async def get_profile_activity_history(
    scope: AccessScope, user: User, pagination: Pagination
) -> Page[StudentActivityRead]:
    authorize(scope, Permission.STUDENT_PROFILE_READ)
    tenant_id = require_student_scope(scope)
    items, total = await _activity_repo.page_for_user(
        tenant_id,
        user.id,
        skip=pagination.offset,
        limit=pagination.limit,
    )
    return Page(
        items=[StudentActivityRead.from_document(row) for row in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )
