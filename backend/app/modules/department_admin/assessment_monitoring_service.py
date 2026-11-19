"""Department Admin — assessment schedule and marks submission monitoring (read-only)."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.core.exceptions import AppError
from app.modules.academics.curriculum_models import EnrollmentRosterEntry
from app.modules.academics.models import PendingAssignmentEvaluation, UpcomingAssessment
from app.modules.auth.models import User
from app.modules.department_admin.assessment_monitoring_logic import (
    batch_counts,
    completion_state,
    deadline_from_metadata,
    overdue_flag,
    student_submission_status,
)
from app.modules.department_admin.department_scope import (
    assert_course_in_department,
    assert_faculty_visible_to_department,
    department_course_codes,
    faculty_user_ids_in_department,
)
from app.modules.department_admin.integrations.department_data_reader import DepartmentDataReader
from app.modules.department_admin.phase5_schemas import (
    AssessmentCompletionRowRead,
    AssessmentMonitoringFilters,
    AssessmentScheduleItemRead,
    AssessmentSummaryRead,
    BatchMarksSubmissionRead,
    FacultyMarksSubmissionRead,
    MarksSubmissionOverviewRead,
    StudentSubmissionStatusRead,
    SubjectMarksSubmissionRead,
)
from app.modules.department_admin.policy import resolve_authorized_department
from app.modules.examinations.enums import MarksBatchStatus, StudentMarkStatus
from app.modules.examinations.grading import get_grading_policy, letter_grade, weighted_percentage
from app.modules.examinations.models import (
    Assessment,
    AssessmentComponent,
    FacultyAssessmentAssignment,
    MarksSubmissionBatch,
    StudentAssessmentMark,
)
from app.modules.students.models import StudentProfile

_reader = DepartmentDataReader()


async def _context(scope: AccessScope, user: User) -> tuple[PydanticObjectId, PydanticObjectId, set[PydanticObjectId], set[str], list[str]]:
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    faculty_ids = await faculty_user_ids_in_department(tenant_id, central_id)
    course_codes = await department_course_codes(tenant_id, central_id)
    programme_codes = [c.upper() for c in institution.programme_codes]
    return tenant_id, central_id, faculty_ids, course_codes, programme_codes


def _apply_programme_batch_filters(
    *,
    programme_code: str | None,
    batch_label: str | None,
    programme_codes: list[str],
) -> None:
    if programme_code and programme_code.upper() not in programme_codes:
        raise AppError(code="FORBIDDEN", message="Programme outside department", status_code=403)


def _assignment_query(
    tenant_id: PydanticObjectId,
    faculty_ids: set[PydanticObjectId],
    course_codes: set[str],
    filters: AssessmentMonitoringFilters,
) -> dict:
    query: dict = {"tenant_id": tenant_id, "course_code": {"$in": list(course_codes)}}
    if faculty_ids:
        query["faculty_user_id"] = {"$in": list(faculty_ids)}
    else:
        query["faculty_user_id"] = {"$in": []}
    if filters.academic_year_label:
        query["academic_year_label"] = filters.academic_year_label
    if filters.semester_label:
        query["semester_label"] = filters.semester_label
    if filters.course_code:
        query["course_code"] = filters.course_code.upper()
    if filters.section_code:
        query["section"] = filters.section_code
    if filters.assessment_id:
        query["assessment_id"] = filters.assessment_id
    if filters.faculty_user_id:
        query["faculty_user_id"] = PydanticObjectId(filters.faculty_user_id)
    return query


async def list_assessments(
    scope: AccessScope,
    user: User,
    *,
    filters: AssessmentMonitoringFilters,
    pagination: Pagination,
) -> Page[AssessmentSummaryRead]:
    authorize(scope, Permission.DEPARTMENT_ASSESSMENT_READ)
    tenant_id, central_id, faculty_ids, course_codes, programme_codes = await _context(scope, user)
    if not course_codes:
        return Page(items=[], total=0, page=pagination.page, page_size=pagination.page_size)
    _apply_programme_batch_filters(
        programme_code=filters.programme_code,
        batch_label=filters.batch_label,
        programme_codes=programme_codes,
    )
    if filters.faculty_user_id:
        await assert_faculty_visible_to_department(
            tenant_id, central_id, PydanticObjectId(filters.faculty_user_id)
        )
    if filters.course_code:
        await assert_course_in_department(tenant_id, central_id, filters.course_code)
    query = _assignment_query(tenant_id, faculty_ids, course_codes, filters)
    db_query = FacultyAssessmentAssignment.find(query).sort([("course_code", 1), ("section", 1)])
    total = await db_query.count()
    rows = await db_query.skip(pagination.skip).limit(pagination.page_size).to_list()
    items: list[AssessmentSummaryRead] = []
    for row in rows:
        assessment = await Assessment.find_one({"tenant_id": tenant_id, "assessment_id": row.assessment_id})
        title = assessment.title if assessment else row.assessment_id
        components = await AssessmentComponent.find(
            {"tenant_id": tenant_id, "assessment_id": row.assessment_id, "faculty_may_enter": True}
        ).to_list()
        enterable_ids = [c.component_id for c in components]
        batches = await MarksSubmissionBatch.find(
            {
                "tenant_id": tenant_id,
                "faculty_user_id": row.faculty_user_id,
                "assessment_id": row.assessment_id,
                "section": row.section,
            }
        ).to_list()
        status_by_component: dict[str, MarksBatchStatus | None] = {cid: None for cid in enterable_ids}
        all_statuses: list[MarksBatchStatus] = []
        for b in batches:
            all_statuses.append(b.status)
            if b.component_id in status_by_component:
                status_by_component[b.component_id] = b.status
        state = completion_state(
            faculty_enterable_component_ids=enterable_ids,
            batch_status_by_component=status_by_component,
            assessment_locked=bool(assessment and assessment.locked),
            final_results_published=bool(assessment and assessment.final_results_published),
        )
        items.append(
            AssessmentSummaryRead(
                assessment_id=row.assessment_id,
                title=title,
                course_code=row.course_code,
                section=row.section,
                faculty_user_id=str(row.faculty_user_id),
                academic_year_label=row.academic_year_label,
                semester_label=row.semester_label,
                programme_code=filters.programme_code,
                batch_label=filters.batch_label,
                completion_state=state,
                marks_batch_summary=batch_counts(all_statuses),
            )
        )
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


async def assessment_schedule(
    scope: AccessScope,
    user: User,
    *,
    filters: AssessmentMonitoringFilters,
    pagination: Pagination,
) -> Page[AssessmentScheduleItemRead]:
    authorize(scope, Permission.DEPARTMENT_ASSESSMENT_READ)
    tenant_id, central_id, faculty_ids, course_codes, programme_codes = await _context(scope, user)
    _apply_programme_batch_filters(
        programme_code=filters.programme_code,
        batch_label=filters.batch_label,
        programme_codes=programme_codes,
    )
    if filters.course_code:
        await assert_course_in_department(tenant_id, central_id, filters.course_code)
    items: list[AssessmentScheduleItemRead] = []
    if faculty_ids:
        upcoming_filters: dict = {
            "tenant_id": tenant_id,
            "faculty_user_id": {"$in": list(faculty_ids)},
            "course_code": {"$in": list(course_codes)},
        }
        if filters.academic_year_label:
            upcoming_filters["academic_year_label"] = filters.academic_year_label
        if filters.semester_label:
            upcoming_filters["semester_label"] = filters.semester_label
        if filters.course_code:
            upcoming_filters["course_code"] = filters.course_code.upper()
        if filters.date_from or filters.date_to:
            scheduled: dict = {}
            if filters.date_from:
                scheduled["$gte"] = filters.date_from
            if filters.date_to:
                scheduled["$lte"] = filters.date_to
            upcoming_filters["scheduled_at"] = scheduled
        for row in await UpcomingAssessment.find(upcoming_filters).sort("scheduled_at").limit(500).to_list():
            if filters.assessment_type and row.assessment_type != filters.assessment_type:
                continue
            deadline = deadline_from_metadata(row.metadata)
            items.append(
                AssessmentScheduleItemRead(
                    source="upcoming_assessment",
                    title=row.title,
                    course_code=row.course_code,
                    section=None,
                    assessment_type=row.assessment_type,
                    scheduled_at=row.scheduled_at,
                    submission_deadline=deadline,
                    deadline_basis="upcoming_assessment_metadata" if deadline else "not_configured",
                    faculty_user_id=str(row.faculty_user_id),
                    academic_year_label=row.academic_year_label,
                    semester_label=row.semester_label,
                    programme_code=filters.programme_code,
                    batch_label=filters.batch_label,
                )
            )
        pending_filters: dict = {
            "tenant_id": tenant_id,
            "faculty_user_id": {"$in": list(faculty_ids)},
        }
        if filters.course_code:
            pending_filters["course_code"] = filters.course_code.upper()
        for row in await PendingAssignmentEvaluation.find(pending_filters).sort("due_at").limit(200).to_list():
            if row.course_code.upper() not in course_codes:
                continue
            items.append(
                AssessmentScheduleItemRead(
                    source="pending_evaluation",
                    title=row.title,
                    course_code=row.course_code,
                    section=None,
                    assessment_type="assignment",
                    scheduled_at=None,
                    submission_deadline=row.due_at,
                    deadline_basis="pending_assignment_evaluation",
                    faculty_user_id=str(row.faculty_user_id),
                    status="pending_evaluation",
                    programme_code=filters.programme_code,
                    batch_label=filters.batch_label,
                )
            )
    total = len(items)
    page_items = items[pagination.skip : pagination.skip + pagination.page_size]
    return Page(items=page_items, total=total, page=pagination.page, page_size=pagination.page_size)


async def assessment_completion(
    scope: AccessScope,
    user: User,
    *,
    filters: AssessmentMonitoringFilters,
    pagination: Pagination,
) -> Page[AssessmentCompletionRowRead]:
    authorize(scope, Permission.DEPARTMENT_ASSESSMENT_READ)
    tenant_id, central_id, faculty_ids, course_codes, programme_codes = await _context(scope, user)
    if not course_codes:
        return Page(items=[], total=0, page=pagination.page, page_size=pagination.page_size)
    _apply_programme_batch_filters(
        programme_code=filters.programme_code,
        batch_label=filters.batch_label,
        programme_codes=programme_codes,
    )
    if filters.course_code:
        await assert_course_in_department(tenant_id, central_id, filters.course_code)
    query = _assignment_query(tenant_id, faculty_ids, course_codes, filters)
    assignments = await FacultyAssessmentAssignment.find(query).to_list()
    rows: list[AssessmentCompletionRowRead] = []
    deadline_cache: dict[str, datetime | None] = {}
    for assign in assignments:
        assessment = await Assessment.find_one({"tenant_id": tenant_id, "assessment_id": assign.assessment_id})
        components = await AssessmentComponent.find(
            {"tenant_id": tenant_id, "assessment_id": assign.assessment_id, "faculty_may_enter": True}
        ).to_list()
        for component in components:
            if filters.assessment_type and component.component_type.value != filters.assessment_type:
                continue
            batch = await MarksSubmissionBatch.find_one(
                {
                    "tenant_id": tenant_id,
                    "faculty_user_id": assign.faculty_user_id,
                    "assessment_id": assign.assessment_id,
                    "component_id": component.component_id,
                    "section": assign.section,
                }
            )
            if assign.assessment_id not in deadline_cache:
                upcoming = await UpcomingAssessment.find_one(
                    {
                        "tenant_id": tenant_id,
                        "faculty_user_id": assign.faculty_user_id,
                        "course_code": assign.course_code,
                    }
                )
                deadline_cache[assign.assessment_id] = (
                    deadline_from_metadata(upcoming.metadata) if upcoming else None
                )
            deadline = deadline_cache[assign.assessment_id]
            st = batch.status if batch else None
            rows.append(
                AssessmentCompletionRowRead(
                    assessment_id=assign.assessment_id,
                    course_code=assign.course_code,
                    section=assign.section,
                    faculty_user_id=str(assign.faculty_user_id),
                    component_id=component.component_id,
                    component_code=component.code,
                    component_type=component.component_type,
                    batch_status=st,
                    batch_id=str(batch.id) if batch else None,
                    submitted_at=batch.submitted_at if batch else None,
                    submission_deadline=deadline,
                    overdue=overdue_flag(deadline=deadline, submitted_at=batch.submitted_at if batch else None, batch_status=st),
                    completion_state=completion_state(
                        faculty_enterable_component_ids=[component.component_id],
                        batch_status_by_component={component.component_id: st},
                        assessment_locked=bool(assessment and assessment.locked),
                        final_results_published=bool(assessment and assessment.final_results_published),
                    ),
                )
            )
    total = len(rows)
    page_items = rows[pagination.skip : pagination.skip + pagination.page_size]
    return Page(items=page_items, total=total, page=pagination.page, page_size=pagination.page_size)


async def marks_submission_overview(
    scope: AccessScope,
    user: User,
    *,
    filters: AssessmentMonitoringFilters,
) -> MarksSubmissionOverviewRead:
    authorize(scope, Permission.DEPARTMENT_ASSESSMENT_READ)
    tenant_id, central_id, faculty_ids, course_codes, programme_codes = await _context(scope, user)
    marks_detail = Permission.DEPARTMENT_ASSESSMENT_MARKS_DETAIL_READ in (scope.effective_permissions or frozenset())
    _apply_programme_batch_filters(
        programme_code=filters.programme_code,
        batch_label=filters.batch_label,
        programme_codes=programme_codes,
    )
    if filters.course_code:
        await assert_course_in_department(tenant_id, central_id, filters.course_code)
    batch_query: dict = {
        "tenant_id": tenant_id,
        "faculty_user_id": {"$in": list(faculty_ids)} if faculty_ids else {"$in": []},
        "course_code": {"$in": list(course_codes)},
    }
    if filters.course_code:
        batch_query["course_code"] = filters.course_code.upper()
    if filters.section_code:
        batch_query["section"] = filters.section_code
    if filters.faculty_user_id:
        batch_query["faculty_user_id"] = PydanticObjectId(filters.faculty_user_id)
    batches = await MarksSubmissionBatch.find(batch_query).to_list()
    totals = batch_counts([b.status for b in batches])
    by_faculty: dict[str, list[MarksBatchStatus]] = defaultdict(list)
    by_subject: dict[str, list[MarksBatchStatus]] = defaultdict(list)
    overdue_by_faculty: dict[str, int] = defaultdict(int)
    for b in batches:
        by_faculty[str(b.faculty_user_id)].append(b.status)
        by_subject[b.course_code].append(b.status)
    pending_by_faculty: dict[str, int] = defaultdict(int)
    if faculty_ids:
        for row in await PendingAssignmentEvaluation.find(
            {"tenant_id": tenant_id, "faculty_user_id": {"$in": list(faculty_ids)}}
        ).to_list():
            if row.course_code.upper() in course_codes:
                pending_by_faculty[str(row.faculty_user_id)] += 1
    faculty_rows: list[FacultyMarksSubmissionRead] = []
    for fid, statuses in sorted(by_faculty.items()):
        fac_user = await User.get(PydanticObjectId(fid))
        faculty_rows.append(
            FacultyMarksSubmissionRead(
                faculty_user_id=fid,
                faculty_name=fac_user.full_name if fac_user else None,
                batch_counts=batch_counts(statuses),
                pending_assignments=pending_by_faculty.get(fid, 0),
                overdue_batches=overdue_by_faculty.get(fid, 0),
            )
        )
    subject_rows = [
        SubjectMarksSubmissionRead(course_code=code, batch_counts=batch_counts(sts), pending_components=0)
        for code, sts in sorted(by_subject.items())
    ]
    batch_map: dict[str, list[MarksBatchStatus]] = defaultdict(list)
    if batches:
        profile_filters: dict = {"tenant_id": tenant_id, "department_id": central_id}
        if filters.programme_code:
            profile_filters["programme_code"] = filters.programme_code.upper()
        if filters.batch_label:
            profile_filters["batch_label"] = filters.batch_label
        if filters.section_code:
            profile_filters["section_code"] = filters.section_code.upper()
        profiles = await StudentProfile.find(profile_filters).limit(10000).to_list()
        sections_for_batch: dict[str, set[str]] = defaultdict(set)
        for p in profiles:
            if p.batch_label and p.section_code:
                sections_for_batch[p.section_code.upper()].add(p.batch_label)
        for b in batches:
            section_key = b.section.upper()
            labels = sections_for_batch.get(section_key) or set()
            if not labels:
                batch_map["unspecified"].append(b.status)
                continue
            for lbl in labels:
                if filters.batch_label and lbl != filters.batch_label:
                    continue
                batch_map[lbl].append(b.status)
    batch_rows = [
        BatchMarksSubmissionRead(batch_label=label, batch_counts=batch_counts(sts), pending_components=0)
        for label, sts in sorted(batch_map.items())
    ]
    year, semester = await _reader.current_academic_term(tenant_id)
    if filters.academic_year_label:
        year = filters.academic_year_label
    if filters.semester_label:
        semester = filters.semester_label
    return MarksSubmissionOverviewRead(
        academic_year_label=year,
        semester_label=semester,
        totals=totals,
        by_faculty=faculty_rows,
        by_subject=subject_rows,
        by_batch=batch_rows,
        marks_detail_visible=marks_detail,
    )


async def student_submission_statuses(
    scope: AccessScope,
    user: User,
    *,
    assessment_id: str,
    component_id: str,
    section: str,
    course_code: str,
    pagination: Pagination,
) -> Page[StudentSubmissionStatusRead]:
    authorize(scope, Permission.DEPARTMENT_ASSESSMENT_READ)
    tenant_id, central_id, faculty_ids, course_codes, _ = await _context(scope, user)
    await assert_course_in_department(tenant_id, central_id, course_code)
    assignment = await FacultyAssessmentAssignment.find_one(
        {
            "tenant_id": tenant_id,
            "assessment_id": assessment_id,
            "section": section,
            "course_code": course_code.upper(),
            "faculty_user_id": {"$in": list(faculty_ids)} if faculty_ids else {"$in": []},
        }
    )
    if assignment is None:
        raise AppError(code="NOT_FOUND", message="Assessment assignment not found in department scope", status_code=404)
    batch = await MarksSubmissionBatch.find_one(
        {
            "tenant_id": tenant_id,
            "assessment_id": assessment_id,
            "component_id": component_id,
            "section": section,
            "faculty_user_id": assignment.faculty_user_id,
        }
    )
    marks_detail = Permission.DEPARTMENT_ASSESSMENT_MARKS_DETAIL_READ in (scope.effective_permissions or frozenset())
    roster = await EnrollmentRosterEntry.find(
        {
            "tenant_id": tenant_id,
            "course_code": course_code.upper(),
            "section_code": section,
        }
    ).to_list()
    allowed_students: list[EnrollmentRosterEntry] = []
    for entry in roster:
        profile = await StudentProfile.find_one(
            Eq(StudentProfile.tenant_id, tenant_id),
            Eq(StudentProfile.user_id, entry.student_user_id),
            Eq(StudentProfile.department_id, central_id),
        )
        if profile is not None:
            allowed_students.append(entry)
    marks_by_student: dict[str, StudentAssessmentMark] = {}
    policy = None
    if batch:
        for m in await StudentAssessmentMark.find({"batch_id": batch.id}).to_list():
            marks_by_student[str(m.student_user_id)] = m
        if marks_detail:
            policy = await get_grading_policy(tenant_id)
    items: list[StudentSubmissionStatusRead] = []
    for entry in allowed_students:
        mark = marks_by_student.get(str(entry.student_user_id))
        status = student_submission_status(
            mark.status.value if mark else None,
            batch_exists=batch is not None,
        )
        row = StudentSubmissionStatusRead(
            student_user_id=str(entry.student_user_id),
            roll_number=entry.roll_number,
            display_name=entry.display_name,
            submission_status=status,
        )
        if marks_detail and mark and policy and mark.status in {StudentMarkStatus.APPROVED, StudentMarkStatus.LOCKED}:
            pct = weighted_percentage(mark.marks_obtained, mark.max_marks)
            row.marks_obtained = mark.marks_obtained
            row.max_marks = mark.max_marks
            row.grade_letter = letter_grade(pct, policy)
        items.append(row)
    total = len(items)
    page_items = items[pagination.skip : pagination.skip + pagination.page_size]
    return Page(items=page_items, total=total, page=pagination.page, page_size=pagination.page_size)