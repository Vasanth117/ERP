"""Parent-facing student profile and academic overview (read-only)."""

from beanie import PydanticObjectId

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.modules.academics.repositories import CourseRepository
from app.modules.auth.models import User
from app.modules.college_admin.models import InstitutionCampus, InstitutionProfile
from app.modules.parents.enums import (
    ParentAcademicEnquiryStatus,
    ParentDataPermission,
)
from app.modules.parents.models import ParentAcademicEnquiry
from app.modules.parents.phase2_schemas import (
    ParentAcademicEnquiryCreate,
    ParentAcademicEnquiryRead,
    ParentAcademicHistoryTermRead,
    ParentAcademicOverviewRead,
    ParentAcademicProgressRead,
    ParentEnrolledCourseRead,
    ParentInstitutionContactRead,
    ParentStudentProfileRead,
)
from app.modules.parents.policy import require_parent_scope
from app.modules.parents.relationship_access import require_student_access
from app.modules.parents.student_context import resolve_student_for_parent
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.models import StudentAcademicRecord, StudentProfile
from app.modules.students.profile_service import _department_name
from app.modules.tenants.models import Tenant

_reader = StudentDataReader()
_course_repo = CourseRepository()
async def _institution_contact(tenant_id: PydanticObjectId) -> ParentInstitutionContactRead | None:
    tenant = await Tenant.get(tenant_id)
    profile = await InstitutionProfile.find_one({"tenant_id": tenant_id})
    name = profile.legal_name if profile else (tenant.name if tenant else None)
    settings_phone = profile.contact_phone if profile else None
    settings_email = profile.institution_email if profile else None
    if not any([name, settings_email, settings_phone]):
        return None
    return ParentInstitutionContactRead(
        institution_name=name,
        primary_email=settings_email,
        primary_phone=settings_phone,
        website=profile.official_website if profile else None,
    )


async def _campus_name(tenant_id: PydanticObjectId) -> str | None:
    campus = await InstitutionCampus.find_one({"tenant_id": tenant_id, "is_main": True})
    if campus is None:
        rows = await InstitutionCampus.find({"tenant_id": tenant_id}).limit(1).to_list()
        campus = rows[0] if rows else None
    return campus.name if campus else None


async def get_student_profile_view(
    scope: AccessScope,
    parent: User,
    student_user_id: str,
    *,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
) -> ParentStudentProfileRead:
    authorize(scope, Permission.PARENT_ACADEMIC_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_PROFILE)
    student = await User.get(sid)
    profile = await StudentProfile.find_one({"tenant_id": tenant_id, "user_id": sid})
    if profile is None or student is None:
        from app.core.exceptions import AppError

        raise AppError(code="NOT_FOUND", message="Student profile not found", status_code=404)
    year, semester = academic_year_label, semester_label
    if not year or not semester:
        ctx = await _reader.current_academic_context(tenant_id)
        if ctx:
            year, semester = ctx.academic_year_label, ctx.semester_label
    dept_name = await _department_name(tenant_id, profile.department_id)
    record = None
    if year and semester:
        record = await StudentAcademicRecord.find_one(
            {"tenant_id": tenant_id, "user_id": sid, "academic_year_label": year, "semester_label": semester}
        )
    enrollment_status = None
    if record:
        enrollment_status = (
            record.enrollment_status.value if hasattr(record.enrollment_status, "value") else str(record.enrollment_status)
        )
    return ParentStudentProfileRead(
        student_user_id=str(sid),
        full_name=student.full_name,
        student_id=profile.student_id,
        roll_number=profile.roll_number,
        admission_number=profile.admission_number,
        admission_date=profile.admission_date,
        profile_photo_ref=profile.profile_photo_ref,
        programme_code=profile.programme_code,
        programme_name=profile.programme_name,
        department_id=str(profile.department_id) if profile.department_id else None,
        department_name=dept_name,
        batch_label=profile.batch_label,
        section_code=profile.section_code,
        academic_year_label=year,
        semester_label=semester,
        enrollment_status=enrollment_status,
        campus_name=await _campus_name(tenant_id),
        institution_contact=await _institution_contact(tenant_id),
    )


async def get_academic_overview(
    scope: AccessScope,
    parent: User,
    student_user_id: str,
    *,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
) -> ParentAcademicOverviewRead:
    authorize(scope, Permission.PARENT_ACADEMIC_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_PROFILE)
    profile_view = await get_student_profile_view(
        scope, parent, student_user_id, academic_year_label=academic_year_label, semester_label=semester_label
    )
    year = profile_view.academic_year_label or academic_year_label
    semester = profile_view.semester_label or semester_label
    if not year or not semester:
        from app.core.exceptions import AppError

        raise AppError(code="ACADEMIC_CONTEXT_MISSING", message="Academic term required", status_code=503)

    roster = await _reader.roster_entries(tenant_id, sid, academic_year_label=year, semester_label=semester)
    courses: list[ParentEnrolledCourseRead] = []
    seen: set[str] = set()
    for entry in roster:
        if entry.course_code in seen:
            continue
        seen.add(entry.course_code)
        course = await _course_repo.get_by_code(tenant_id, entry.course_code)
        courses.append(
            ParentEnrolledCourseRead(
                course_code=entry.course_code,
                course_name=course.name if course else entry.course_code,
                section_code=entry.section_code,
                credit_units=course.credit_units if course else None,
                academic_year_label=year,
                semester_label=semester,
            )
        )

    progress: ParentAcademicProgressRead | None = None
    rel, perms = await require_student_access(tenant_id, parent.id, sid)
    if perms and perms.grants.get(ParentDataPermission.VIEW_RESULTS.value, False):
        record = await StudentAcademicRecord.find_one(
            {"tenant_id": tenant_id, "user_id": sid, "academic_year_label": year, "semester_label": semester}
        )
        if record:
            notices: list[str] = []
            standing = record.academic_standing.value if hasattr(record.academic_standing, "value") else str(
                record.academic_standing
            )
            if standing and standing not in {"unknown", "good"}:
                notices.append(f"Academic standing: {standing}")
            progress = ParentAcademicProgressRead(
                academic_standing=standing,
                progression_status=record.progression_status.value
                if hasattr(record.progression_status, "value")
                else str(record.progression_status),
                cgpa=record.cgpa,
                credits_registered=record.credits_registered,
                credits_earned=record.credits_earned,
                notices=notices,
            )

    return ParentAcademicOverviewRead(profile=profile_view, enrolled_courses=courses, progress=progress)


async def list_academic_history(
    scope: AccessScope,
    parent: User,
    student_user_id: str,
    pagination: Pagination,
) -> Page[ParentAcademicHistoryTermRead]:
    authorize(scope, Permission.PARENT_ACADEMIC_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_PROFILE)
    records = await StudentAcademicRecord.find({"tenant_id": tenant_id, "user_id": sid}).sort(
        "-academic_year_label", "-semester_label"
    ).skip(pagination.offset).limit(pagination.limit).to_list()
    total = await StudentAcademicRecord.find({"tenant_id": tenant_id, "user_id": sid}).count()
    items = [
        ParentAcademicHistoryTermRead(
            academic_year_label=r.academic_year_label,
            semester_label=r.semester_label,
            enrollment_status=r.enrollment_status.value if hasattr(r.enrollment_status, "value") else str(r.enrollment_status),
            credits_registered=r.credits_registered,
            credits_earned=r.credits_earned,
            cgpa=r.cgpa,
            summary=r.eligibility_summary,
        )
        for r in records
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def submit_academic_enquiry(
    scope: AccessScope,
    parent: User,
    student_user_id: str,
    payload: ParentAcademicEnquiryCreate,
) -> ParentAcademicEnquiryRead:
    authorize(scope, Permission.PARENT_ACADEMIC_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_PROFILE)
    rel, _ = await require_student_access(tenant_id, parent.id, sid, ParentDataPermission.VIEW_PROFILE)
    doc = ParentAcademicEnquiry(
        tenant_id=tenant_id,
        parent_user_id=parent.id,
        student_user_id=sid,
        relationship_id=rel.id,
        category=payload.category,
        description=payload.description.strip(),
        requested_fields=payload.requested_fields,
        status=ParentAcademicEnquiryStatus.SUBMITTED.value,
    )
    await doc.insert()
    return ParentAcademicEnquiryRead(
        enquiry_id=str(doc.id),
        category=doc.category,
        description=doc.description,
        status=doc.status,
        response_notes=doc.response_notes,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


async def list_academic_enquiries(
    scope: AccessScope, parent: User, student_user_id: str
) -> list[ParentAcademicEnquiryRead]:
    authorize(scope, Permission.PARENT_ACADEMIC_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_PROFILE)
    rows = await ParentAcademicEnquiry.find(
        {"tenant_id": tenant_id, "parent_user_id": parent.id, "student_user_id": sid}
    ).sort("-created_at").to_list()
    return [
        ParentAcademicEnquiryRead(
            enquiry_id=str(r.id),
            category=r.category,
            description=r.description,
            status=r.status,
            response_notes=r.response_notes,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in rows
    ]