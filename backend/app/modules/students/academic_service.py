"""Student academic and enrollment views (read) plus permitted requests."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.students.enums import (
    StudentAcademicRequestStatus,
    StudentAcademicRequestType,
    StudentActivityType,
)
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.models import StudentAcademicRequest
from app.modules.students.policy import require_student_scope
from app.modules.academics.curriculum_models import CourseRecord
from app.modules.academics.models import AcademicYearContext
from app.modules.students.profile_service import _department_name, _load_admission, ensure_student_profile
from app.modules.students.repositories import (
    StudentAcademicRecordRepository,
    StudentActivityRepository,
    StudentEnrollmentHistoryRepository,
    StudentEnrollmentRepository,
)
from app.modules.students.schemas import (
    AcademicDetailsRead,
    AcademicEligibilityRead,
    AdmissionInfoRead,
    DepartmentProgrammeRead,
    EnrollmentHistoryRead,
    EnrollmentLineRead,
    EnrollmentRequestCreate,
    EnrollmentRequestRead,
    EnrollmentStatusRead,
    StudentAcademicAdvisorRead,
    StudentAcademicInformationRead,
    enrollment_history_from_doc,
    enrollment_line_from_doc,
    enrollment_status_from_record,
    request_from_doc,
)

_reader = StudentDataReader()
_enrollment_repo = StudentEnrollmentRepository()
_history_repo = StudentEnrollmentHistoryRepository()
_record_repo = StudentAcademicRecordRepository()
_activity_repo = StudentActivityRepository()

_PERMITTED_REQUEST_TYPES = frozenset(
    {
        StudentAcademicRequestType.SECTION_CHANGE,
        StudentAcademicRequestType.COURSE_ADD,
        StudentAcademicRequestType.COURSE_DROP,
        StudentAcademicRequestType.LEAVE_OF_ABSENCE,
        StudentAcademicRequestType.OTHER,
    }
)


def _batch_display_label(batch_label: str | None, metadata: dict) -> str | None:
    if not batch_label:
        return None
    explicit = metadata.get("batch_display")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    raw = batch_label.strip()
    if "–" in raw or ("-" in raw and len(raw) > 6):
        return raw.replace("-", "–")
    try:
        start = int(raw[:4])
        duration = metadata.get("programme_duration_years")
        years = int(duration) if duration is not None else 4
        return f"{start}–{start + years}"
    except (TypeError, ValueError):
        return raw


async def _programme_regulation(tenant_id: PydanticObjectId, programme_code: str | None) -> str | None:
    if not programme_code:
        return None
    course = await CourseRecord.find_one(
        Eq(CourseRecord.tenant_id, tenant_id),
        Eq(CourseRecord.course_code, programme_code),
    )
    if course is None or not course.regulation_label:
        return None
    return course.regulation_label


async def _current_semester_number(tenant_id: PydanticObjectId) -> int | None:
    context = await AcademicYearContext.find_one(
        Eq(AcademicYearContext.tenant_id, tenant_id),
        Eq(AcademicYearContext.is_current, True),
    )
    if context is None:
        return None
    return context.semester_number


async def _resolve_term_labels(tenant_id: PydanticObjectId) -> tuple[str, str]:
    """Returns current year/semester labels, or placeholders when the college has not set a term."""
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        return "N/A", "N/A"
    return context.academic_year_label, context.semester_label


async def get_academic_details(scope: AccessScope, user: User) -> AcademicDetailsRead:
    authorize(scope, Permission.STUDENT_ACADEMIC_READ)
    tenant_id = require_student_scope(scope)
    profile = await ensure_student_profile(scope, user)
    department_name = await _department_name(tenant_id, profile.department_id)
    year, semester = await _resolve_term_labels(tenant_id)

    admission = AdmissionInfoRead(
        student_id=profile.student_id,
        roll_number=profile.roll_number,
        admission_number=profile.admission_number,
        admission_date=profile.admission_date,
        programme_code=profile.programme_code,
        programme_name=profile.programme_name,
        department_name=department_name,
        batch_label=profile.batch_label,
        section_code=profile.section_code,
    )

    record = await _record_repo.get_current(tenant_id, user.id, academic_year_label=year, semester_label=semester)
    enrollment_status = enrollment_status_from_record(record, year=year, semester=semester)

    department_programme = DepartmentProgrammeRead(
        department_id=str(profile.department_id) if profile.department_id else None,
        department_name=department_name,
        programme_code=profile.programme_code,
        programme_name=profile.programme_name,
        batch_label=profile.batch_label,
        section_code=profile.section_code,
    )

    current_lines: list[EnrollmentLineRead] = []
    if year != "N/A" and semester != "N/A":
        enrollments = await _enrollment_repo.list_for_term(
            tenant_id, user.id, academic_year_label=year, semester_label=semester
        )
        if enrollments:
            current_lines = [enrollment_line_from_doc(row) for row in enrollments]
        else:
            roster = await _reader.roster_entries(
                tenant_id, user.id, academic_year_label=year, semester_label=semester
            )
            current_lines = [
                EnrollmentLineRead(
                    course_code=r.course_code,
                    course_name=r.course_code,
                    section_code=r.section_code,
                    status=enrollment_status.enrollment_status,
                    academic_year_label=year,
                    semester_label=semester,
                )
                for r in roster
            ]

    academic_record = None
    if record is not None:
        academic_record = AcademicEligibilityRead(
            promotion_eligible=record.promotion_eligible,
            eligibility_summary=record.eligibility_summary,
            credits_registered=record.credits_registered,
            credits_earned=record.credits_earned,
            cgpa=record.cgpa,
        )

    admission_doc = await _load_admission(tenant_id, user.id, profile)
    meta = admission_doc.metadata if admission_doc is not None else {}
    regulation = meta.get("regulation_label") if isinstance(meta.get("regulation_label"), str) else None
    if not regulation:
        regulation = await _programme_regulation(tenant_id, profile.programme_code)
    admission_type = meta.get("admission_type") if isinstance(meta.get("admission_type"), str) else None

    academic_information = StudentAcademicInformationRead(
        regulation_label=regulation,
        admission_type=admission_type,
        batch_display=_batch_display_label(profile.batch_label or admission_doc.batch_label if admission_doc else None, meta),
        current_semester_number=await _current_semester_number(tenant_id),
    )
    advisors = StudentAcademicAdvisorRead(
        class_advisor_name=meta.get("class_advisor_name") if isinstance(meta.get("class_advisor_name"), str) else None,
        mentor_name=meta.get("mentor_name") if isinstance(meta.get("mentor_name"), str) else None,
    )

    return AcademicDetailsRead(
        admission=admission,
        enrollment_status=enrollment_status,
        department_programme=department_programme,
        current_enrollments=current_lines,
        academic_record=academic_record,
        academic_information=academic_information,
        advisors=advisors,
    )


async def get_enrollment_history(scope: AccessScope, user: User, pagination: Pagination) -> Page[EnrollmentHistoryRead]:
    authorize(scope, Permission.STUDENT_ENROLLMENT_READ)
    tenant_id = require_student_scope(scope)
    skip = (pagination.page - 1) * pagination.page_size
    items, total = await _history_repo.list_for_user(tenant_id, user.id, skip=skip, limit=pagination.page_size)
    return Page(
        items=[enrollment_history_from_doc(row) for row in items],
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )


async def get_enrollment_status(scope: AccessScope, user: User) -> EnrollmentStatusRead:
    authorize(scope, Permission.STUDENT_ENROLLMENT_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _resolve_term_labels(tenant_id)
    record = await _record_repo.get_current(tenant_id, user.id, academic_year_label=year, semester_label=semester)
    return enrollment_status_from_record(record, year=year, semester=semester)


async def get_academic_eligibility(scope: AccessScope, user: User) -> AcademicEligibilityRead:
    authorize(scope, Permission.STUDENT_ACADEMIC_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _resolve_term_labels(tenant_id)
    record = await _record_repo.get_current(tenant_id, user.id, academic_year_label=year, semester_label=semester)
    if record is None:
        return AcademicEligibilityRead()
    return AcademicEligibilityRead(
        promotion_eligible=record.promotion_eligible,
        eligibility_summary=record.eligibility_summary,
        credits_registered=record.credits_registered,
        credits_earned=record.credits_earned,
        cgpa=record.cgpa,
    )


async def submit_enrollment_request(scope: AccessScope, user: User, payload: EnrollmentRequestCreate) -> EnrollmentRequestRead:
    authorize(scope, Permission.STUDENT_ENROLLMENT_REQUEST)
    tenant_id = require_student_scope(scope)
    if payload.request_type not in _PERMITTED_REQUEST_TYPES:
        raise AppError(code="FORBIDDEN", message="This request type cannot be submitted by students", status_code=403)
    year, semester = await _resolve_term_labels(tenant_id)
    doc = StudentAcademicRequest(
        tenant_id=tenant_id,
        user_id=user.id,
        request_type=payload.request_type,
        academic_year_label=year,
        semester_label=semester,
        title=payload.title.strip(),
        description=payload.description.strip(),
        payload=payload.payload,
        status=StudentAcademicRequestStatus.SUBMITTED,
    )
    await doc.insert()
    await record_audit(
        actor_id=scope.user_id,
        action="student.enrollment_request.submitted",
        resource_type="student_academic_request",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        metadata={"request_type": payload.request_type.value},
    )
    await _activity_repo.append(
        tenant_id=tenant_id,
        user_id=user.id,
        activity_type=StudentActivityType.ENROLLMENT_REQUEST,
        title=f"Enrollment request: {payload.title}",
        description=payload.request_type.value,
    )
    return request_from_doc(doc)


async def get_enrollment_request_status(scope: AccessScope, user: User, request_id: str) -> EnrollmentRequestRead:
    authorize(scope, Permission.STUDENT_ENROLLMENT_READ)
    tenant_id = require_student_scope(scope)
    doc_id = to_object_id(request_id, "request id")
    doc = await StudentAcademicRequest.get(doc_id)
    if doc is None or str(doc.tenant_id) != str(tenant_id) or str(doc.user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Enrollment request not found", status_code=404)
    return request_from_doc(doc)


async def list_enrollment_requests(scope: AccessScope, user: User, pagination: Pagination) -> Page[EnrollmentRequestRead]:
    authorize(scope, Permission.STUDENT_ENROLLMENT_READ)
    tenant_id = require_student_scope(scope)
    skip = (pagination.page - 1) * pagination.page_size
    query = StudentAcademicRequest.find({"tenant_id": tenant_id, "user_id": user.id}).sort("-submitted_at")
    total = await query.count()
    items = await query.skip(skip).limit(pagination.page_size).to_list()
    return Page(
        items=[request_from_doc(row) for row in items],
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )
