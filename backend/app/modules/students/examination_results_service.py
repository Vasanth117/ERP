"""Student semester examination results (published only)."""

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.examinations.examination_registration_enums import SemesterResultPublicationStatus
from app.modules.students.examination_registration_models import StudentResultNotification, StudentResultViewPreferences
from app.modules.students.examination_results_schemas import (
    ArrearResultRead,
    ResultAttemptHistoryRead,
    ResultNotificationRead,
    ResultPublicationStatusRead,
    SemesterResultSummaryRead,
    SubjectWiseMarksRead,
)
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.integrations.examination_results_reader import (
    arrear_results,
    published_result_bundle,
    published_subject_marks,
    result_publication_status,
)
from app.modules.students.policy import require_student_scope

_reader = StudentDataReader()


async def _term(tenant_id: PydanticObjectId) -> tuple[str, str]:
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        raise AppError(code="ACADEMIC_CONTEXT_MISSING", message="Academic year not configured", status_code=503)
    return context.academic_year_label, context.semester_label


async def _prefs(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> StudentResultViewPreferences:
    row = await StudentResultViewPreferences.find_one({"tenant_id": tenant_id, "user_id": user_id})
    if row is not None:
        return row
    row = StudentResultViewPreferences(tenant_id=tenant_id, user_id=user_id)
    await row.insert()
    return row


def _subject_line_to_read(line) -> SubjectWiseMarksRead:
    return SubjectWiseMarksRead(
        season_id=line.season_id,
        course_code=line.course_code,
        course_name=line.course_name,
        attempt_number=line.attempt_number,
        is_arrear=line.is_arrear,
        theory_obtained=line.theory_obtained,
        theory_max=line.theory_max,
        practical_obtained=line.practical_obtained,
        practical_max=line.practical_max,
        internal_obtained=line.internal_obtained,
        internal_max=line.internal_max,
        external_obtained=line.external_obtained,
        external_max=line.external_max,
        total_obtained=line.total_obtained,
        total_max=line.total_max,
        pass_fail=line.pass_fail,
        grade_letter=line.grade_letter,
        published_at=line.published_at,
    )


async def get_published_semester_results(scope: AccessScope, user: User, season_id: str) -> SemesterResultSummaryRead:
    authorize(scope, Permission.STUDENT_EXAM_RESULTS_READ)
    tenant_id = require_student_scope(scope)
    bundle = await published_result_bundle(tenant_id, user.id, season_id)
    if bundle is None:
        raise AppError(code="NOT_FOUND", message="Published results not available", status_code=404)
    await record_audit(
        actor_id=scope.user_id,
        action="student.exam_results.viewed",
        resource_type="semester_result_publication",
        resource_id=season_id,
        tenant_id=tenant_id,
    )
    return SemesterResultSummaryRead(
        season_id=bundle.season_id,
        academic_year_label=bundle.academic_year_label,
        semester_label=bundle.semester_label,
        overall_pass=bundle.overall_pass,
        gpa=bundle.gpa,
        published_at=bundle.published_at,
        status=bundle.status.value,
    )


async def get_subject_wise_marks(scope: AccessScope, user: User, season_id: str | None = None) -> list[SubjectWiseMarksRead]:
    authorize(scope, Permission.STUDENT_EXAM_RESULTS_READ)
    tenant_id = require_student_scope(scope)
    if season_id:
        bundle = await published_result_bundle(tenant_id, user.id, season_id)
        if bundle is None:
            raise AppError(code="NOT_FOUND", message="Published results not available", status_code=404)
    lines = await published_subject_marks(tenant_id, user.id, season_id=season_id)
    return [_subject_line_to_read(line) for line in lines]


async def get_attempt_history(scope: AccessScope, user: User, pagination: Pagination) -> Page[ResultAttemptHistoryRead]:
    authorize(scope, Permission.STUDENT_EXAM_RESULTS_READ)
    tenant_id = require_student_scope(scope)
    await _prefs(tenant_id, user.id)
    lines = await published_subject_marks(tenant_id, user.id)
    items = [
        ResultAttemptHistoryRead(
            season_id=line.season_id,
            course_code=line.course_code,
            attempt_number=line.attempt_number,
            pass_fail=line.pass_fail,
            total_obtained=line.total_obtained,
            total_max=line.total_max,
            published_at=line.published_at,
        )
        for line in lines
    ]
    slice_items = items[pagination.offset : pagination.offset + pagination.limit]
    return Page(items=slice_items, total=len(items), limit=pagination.limit, offset=pagination.offset)


async def get_arrear_results(scope: AccessScope, user: User) -> list[ArrearResultRead]:
    authorize(scope, Permission.STUDENT_EXAM_RESULTS_READ)
    tenant_id = require_student_scope(scope)
    lines = await arrear_results(tenant_id, user.id)
    return [
        ArrearResultRead(
            season_id=line.season_id,
            course_code=line.course_code,
            course_name=line.course_name,
            attempt_number=line.attempt_number,
            pass_fail=line.pass_fail,
            total_obtained=line.total_obtained,
            total_max=line.total_max,
            published_at=line.published_at,
        )
        for line in lines
    ]


async def get_result_publication_status(scope: AccessScope, user: User, season_id: str) -> ResultPublicationStatusRead:
    authorize(scope, Permission.STUDENT_EXAM_RESULTS_READ)
    tenant_id = require_student_scope(scope)
    doc = await result_publication_status(tenant_id, user.id, season_id)
    if doc is None:
        return ResultPublicationStatusRead(season_id=season_id, status="not_available", message="No result record")
    if doc.status == SemesterResultPublicationStatus.PUBLISHED:
        message = "Results published"
    elif doc.status == SemesterResultPublicationStatus.PROCESSING:
        message = "Results are being processed"
    else:
        message = "Results withheld"
    return ResultPublicationStatusRead(
        season_id=season_id,
        status=doc.status.value,
        published_at=doc.published_at if doc.status == SemesterResultPublicationStatus.PUBLISHED else None,
        message=message,
    )


async def get_result_notifications(scope: AccessScope, user: User, pagination: Pagination) -> Page[ResultNotificationRead]:
    authorize(scope, Permission.STUDENT_EXAM_RESULTS_READ)
    tenant_id = require_student_scope(scope)
    query = StudentResultNotification.find({"tenant_id": tenant_id, "user_id": user.id}).sort("-created_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            ResultNotificationRead(
                id=str(r.id),
                kind=r.kind.value,
                season_id=r.season_id,
                title=r.title,
                body=r.body,
                created_at=r.created_at,
                read_at=r.read_at,
            )
            for r in rows
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )
