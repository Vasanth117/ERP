"""Published grades, GPA, CGPA, and credits (read-only)."""

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.examinations.grading_gpa import gpa_breakdown_lines, policy_for_tenant
from app.modules.examinations.models import GradingPolicy
from app.modules.students.academic_grading_schemas import (
    AcademicStandingRead,
    CgpaRead,
    CreditSummaryRead,
    GpaCalculationBreakdownRead,
    GradeHistoryItemRead,
    SemesterGpaRead,
    SemesterPerformanceRead,
    SubjectGradeRead,
)
from app.modules.students.enums import AcademicStanding
from app.modules.students.integrations.academic_grading_reader import (
    academic_standing_record,
    cgpa_calculated,
    derive_standing,
    lines_for_season,
    published_publications,
    published_subject_lines,
    semester_gpa_calculated,
    to_graded_lines,
)
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.policy import require_student_scope
from app.modules.students.profile_service import ensure_student_profile

_reader = StudentDataReader()

PROGRAMME_CREDIT_DEFAULT = 160.0


async def _term(tenant_id: PydanticObjectId) -> tuple[str, str]:
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        raise AppError(code="ACADEMIC_CONTEXT_MISSING", message="Academic year not configured", status_code=503)
    return context.academic_year_label, context.semester_label


def _policy_version(policy: GradingPolicy) -> str:
    return str(int(policy.updated_at.timestamp()))


async def get_subject_grades(scope: AccessScope, user: User, season_id: str | None = None) -> list[SubjectGradeRead]:
    authorize(scope, Permission.STUDENT_GRADES_READ)
    tenant_id = require_student_scope(scope)
    filters: dict = {"tenant_id": tenant_id, "student_user_id": user.id, "published": True}
    if season_id:
        filters["season_id"] = season_id
    from app.modules.examinations.result_publication_models import SemesterResultSubjectMark

    rows = await SemesterResultSubjectMark.find(filters).sort("course_code").to_list()
    return [
        SubjectGradeRead(
            season_id=r.season_id,
            course_code=r.course_code,
            course_name=r.course_name,
            grade_letter=r.grade_letter,
            grade_points=r.grade_points,
            credit_units=r.credit_units,
            pass_fail=r.pass_fail,
            published_at=r.published_at,
            grading_policy_version=r.grading_policy_version,
        )
        for r in rows
    ]


async def get_semester_gpa(scope: AccessScope, user: User, season_id: str) -> SemesterGpaRead:
    authorize(scope, Permission.STUDENT_GRADES_READ)
    tenant_id = require_student_scope(scope)
    pub = next((p for p in await published_publications(tenant_id, user.id) if p.season_id == season_id), None)
    if pub is None:
        raise AppError(code="NOT_FOUND", message="Published semester results not found", status_code=404)
    lines = await lines_for_season(tenant_id, user.id, season_id)
    calculated = await semester_gpa_calculated(tenant_id, user.id, season_id)
    earned = sum(line.credit_units for line in lines if (line.pass_fail or "").lower() == "pass")
    attempted = sum(line.credit_units for line in lines)
    return SemesterGpaRead(
        season_id=season_id,
        academic_year_label=pub.academic_year_label,
        semester_label=pub.semester_label,
        gpa=calculated,
        official_gpa=pub.gpa,
        credits_attempted=attempted,
        credits_earned=earned,
        grading_policy_version=pub.grading_policy_version,
    )


async def get_cgpa(scope: AccessScope, user: User) -> CgpaRead:
    authorize(scope, Permission.STUDENT_GRADES_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    record = await academic_standing_record(tenant_id, user.id, year, semester)
    calculated = await cgpa_calculated(tenant_id, user.id)
    policy = await policy_for_tenant(tenant_id)
    earned = record.credits_earned if record else 0.0
    required = record.eligibility_summary.get("credits_required", PROGRAMME_CREDIT_DEFAULT) if record else PROGRAMME_CREDIT_DEFAULT
    pending = max(required - earned, 0.0) if required else None
    return CgpaRead(
        cgpa=calculated or (record.cgpa if record else None),
        credits_earned=earned,
        credits_required=required,
        credits_pending=pending,
        grading_policy_version=_policy_version(policy),
    )


async def get_semester_performance(scope: AccessScope, user: User) -> list[SemesterPerformanceRead]:
    authorize(scope, Permission.STUDENT_GRADES_READ)
    tenant_id = require_student_scope(scope)
    pubs = await published_publications(tenant_id, user.id)
    items: list[SemesterPerformanceRead] = []
    for pub in pubs:
        gpa = await semester_gpa_calculated(tenant_id, user.id, pub.season_id)
        items.append(
            SemesterPerformanceRead(
                season_id=pub.season_id,
                academic_year_label=pub.academic_year_label,
                semester_label=pub.semester_label,
                gpa=pub.gpa or gpa,
                overall_pass=pub.overall_pass,
                published_at=pub.published_at,
            )
        )
    return items


async def get_grade_history(scope: AccessScope, user: User, pagination: Pagination) -> Page[GradeHistoryItemRead]:
    authorize(scope, Permission.STUDENT_GRADES_READ)
    tenant_id = require_student_scope(scope)
    rows = await published_subject_lines(tenant_id, user.id)
    items = [
        GradeHistoryItemRead(
            season_id=r.season_id,
            course_code=r.course_code,
            grade_letter=r.grade_letter,
            grade_points=r.grade_points,
            attempt_number=r.attempt_number,
            published_at=r.published_at,
        )
        for r in rows
    ]
    slice_items = items[pagination.offset : pagination.offset + pagination.limit]
    return Page(items=slice_items, total=len(items), limit=pagination.limit, offset=pagination.offset)


async def get_credit_summary(scope: AccessScope, user: User) -> CreditSummaryRead:
    authorize(scope, Permission.STUDENT_GRADES_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    record = await academic_standing_record(tenant_id, user.id, year, semester)
    marks = await published_subject_lines(tenant_id, user.id)
    lines = await to_graded_lines(tenant_id, marks)
    earned_from_grades = sum(
        line.credit_units for line in lines if (line.pass_fail or "").lower() == "pass"
    )
    earned = record.credits_earned if record and record.credits_earned else earned_from_grades
    registered = record.credits_registered if record else 0.0
    required = record.eligibility_summary.get("credits_required", PROGRAMME_CREDIT_DEFAULT) if record else PROGRAMME_CREDIT_DEFAULT
    pending = max(required - earned, 0.0)
    pct = round((earned / required) * 100, 2) if required else None
    return CreditSummaryRead(
        credits_earned=earned,
        credits_registered=registered,
        credits_pending=pending,
        credits_required=required,
        completion_percentage=pct,
    )


async def get_academic_standing(scope: AccessScope, user: User) -> AcademicStandingRead:
    authorize(scope, Permission.STUDENT_GRADES_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    record = await academic_standing_record(tenant_id, user.id, year, semester)
    profile = await ensure_student_profile(scope, user)
    standing = derive_standing(record)
    return AcademicStandingRead(
        standing=standing,
        programme_code=profile.programme_code,
        promotion_eligible=record.promotion_eligible if record else None,
        probation=standing == AcademicStanding.PROBATION,
    )


async def get_gpa_breakdown(scope: AccessScope, user: User, season_id: str | None = None) -> GpaCalculationBreakdownRead:
    authorize(scope, Permission.STUDENT_GRADES_READ)
    tenant_id = require_student_scope(scope)
    policy = await policy_for_tenant(tenant_id)
    if season_id:
        lines = await lines_for_season(tenant_id, user.id, season_id)
        semester_gpa = await semester_gpa_calculated(tenant_id, user.id, season_id)
        cgpa = None
    else:
        marks = await published_subject_lines(tenant_id, user.id)
        lines = await to_graded_lines(tenant_id, marks)
        semester_gpa = None
        cgpa = await cgpa_calculated(tenant_id, user.id)
    await record_audit(
        actor_id=scope.user_id,
        action="student.gpa.breakdown_viewed",
        resource_type="student_user",
        resource_id=str(user.id),
        tenant_id=tenant_id,
    )
    return GpaCalculationBreakdownRead(
        season_id=season_id,
        lines=gpa_breakdown_lines(lines),
        semester_gpa=semester_gpa,
        cgpa=cgpa,
        grading_policy_version=_policy_version(policy),
    )
