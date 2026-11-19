"""Department Admin — academic performance monitoring (read-only aggregates)."""

from __future__ import annotations

from collections import defaultdict

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.department_admin.assessment_monitoring_service import _context
from app.modules.department_admin.attendance_oversight_service import attendance_shortages
from app.modules.department_admin.department_scope import assert_course_in_department, department_course_codes
from app.modules.department_admin.integrations.department_data_reader import DepartmentDataReader
from app.modules.department_admin.models import DepartmentStudentFollowUp
from app.modules.department_admin.performance_monitoring_logic import (
    DEFAULT_SUPPORT_INDICATORS,
    PERFORMANCE_FOLLOW_UP_CATEGORIES,
    normalize_pass_fail,
    pass_percentage,
    period_label,
)
from app.modules.department_admin.performance_schemas import (
    ArrearStudentRead,
    ArrearSummaryRead,
    BatchPerformanceRead,
    PassFailSummaryRead,
    PerformanceFilters,
    PerformanceFollowUpRead,
    PerformanceMeta,
    PerformanceOverviewRead,
    PerformanceTrendsRead,
    ProgrammePerformanceRead,
    ProgressionStudentRead,
    StudentSupportRead,
    StudentsRequiringSupportRead,
    SubjectPerformanceRead,
    SupportFlagRead,
    TrendPeriodRead,
)
from app.modules.department_admin.policy import resolve_authorized_department
from app.modules.examinations.examination_registration_enums import SemesterResultPublicationStatus
from app.modules.examinations.result_publication_models import SemesterResultPublication, SemesterResultSubjectMark
from app.modules.students.arrear_backlog_enums import BacklogStatus
from app.modules.students.arrear_backlog_models import StudentArrearReference
from app.modules.students.enums import AcademicStanding, StudentEnrollmentStatus
from app.modules.students.models import StudentAcademicRecord, StudentEnrollment, StudentProfile

_reader = DepartmentDataReader()


async def _profile_query(
    tenant_id: PydanticObjectId,
    central_id: PydanticObjectId,
    filters: PerformanceFilters,
) -> dict:
    query: dict = {"tenant_id": tenant_id, "department_id": central_id}
    if filters.programme_code:
        query["programme_code"] = filters.programme_code.upper()
    if filters.batch_label:
        query["batch_label"] = filters.batch_label
    if filters.section_code:
        query["section_code"] = filters.section_code.upper()
    return query


async def _dept_profiles(
    tenant_id: PydanticObjectId,
    central_id: PydanticObjectId,
    filters: PerformanceFilters,
) -> list[StudentProfile]:
    return await StudentProfile.find(await _profile_query(tenant_id, central_id, filters)).limit(15000).to_list()


def _meta(
    filters: PerformanceFilters,
    *,
    basis: str,
    count: int,
    excluded: dict[str, int] | None = None,
) -> PerformanceMeta:
    return PerformanceMeta(
        academic_year_label=filters.academic_year_label,
        semester_label=filters.semester_label,
        season_id=filters.season_id,
        calculation_basis=basis,
        included_student_count=count,
        excluded_reason_counts=excluded or {},
    )


def _result_line_query(
    tenant_id: PydanticObjectId,
    student_ids: list[PydanticObjectId],
    filters: PerformanceFilters,
) -> dict:
    query: dict = {
        "tenant_id": tenant_id,
        "student_user_id": {"$in": student_ids},
        "published": True,
    }
    if filters.season_id:
        query["season_id"] = filters.season_id
    if filters.course_code:
        query["course_code"] = filters.course_code.upper()
    return query


async def performance_overview(scope: AccessScope, user: User, *, filters: PerformanceFilters) -> PerformanceOverviewRead:
    authorize(scope, Permission.DEPARTMENT_PERFORMANCE_READ)
    tenant_id, central_id, _, _, programme_codes = await _context(scope, user)
    if filters.programme_code and filters.programme_code.upper() not in programme_codes:
        raise AppError(code="FORBIDDEN", message="Programme outside department", status_code=403)
    profiles = await _dept_profiles(tenant_id, central_id, filters)
    student_ids = [p.user_id for p in profiles]
    enrolled = len(profiles)
    excluded: dict[str, int] = defaultdict(int)
    pass_c = fail_c = unknown = 0
    pending_pub = withheld = 0
    students_with_results: set[str] = set()
    if student_ids:
        pub_query: dict = {"tenant_id": tenant_id, "student_user_id": {"$in": student_ids}}
        if filters.season_id:
            pub_query["season_id"] = filters.season_id
        for pub in await SemesterResultPublication.find(pub_query).to_list():
            if pub.status == SemesterResultPublicationStatus.PUBLISHED:
                students_with_results.add(str(pub.student_user_id))
            elif pub.status == SemesterResultPublicationStatus.WITHHELD:
                withheld += 1
                excluded["result_withheld"] += 1
            else:
                pending_pub += 1
                excluded["result_pending"] += 1
        lines = await SemesterResultSubjectMark.find(_result_line_query(tenant_id, student_ids, filters)).to_list()
        course_codes = await department_course_codes(tenant_id, central_id)
        for line in lines:
            if line.course_code.upper() not in course_codes:
                continue
            norm = normalize_pass_fail(line.pass_fail)
            if norm == "pass":
                pass_c += 1
            elif norm == "fail":
                fail_c += 1
            elif norm is None:
                excluded["result_line_missing_outcome"] += 1
            else:
                unknown += 1
    return PerformanceOverviewRead(
        meta=_meta(filters, basis="semester_result_subject_marks.published+pass_fail", count=enrolled, excluded=dict(excluded)),
        enrolled_students=enrolled,
        students_with_published_results=len(students_with_results),
        result_pending_count=pending_pub,
        result_withheld_count=withheld,
        pass_count=pass_c,
        fail_count=fail_c,
        pass_percentage=pass_percentage(pass_c, fail_c),
        unknown_outcome_count=unknown,
    )


async def performance_programmes(scope: AccessScope, user: User, *, filters: PerformanceFilters) -> list[ProgrammePerformanceRead]:
    authorize(scope, Permission.DEPARTMENT_PERFORMANCE_READ)
    tenant_id, central_id, _, _, _ = await _context(scope, user)
    profiles = await _dept_profiles(tenant_id, central_id, filters)
    by_prog: dict[str, list[StudentProfile]] = defaultdict(list)
    for p in profiles:
        code = (p.programme_code or "unknown").upper()
        by_prog[code].append(p)
    student_ids = [p.user_id for p in profiles]
    lines = await SemesterResultSubjectMark.find(_result_line_query(tenant_id, student_ids, filters)).to_list() if student_ids else []
    stats: dict[str, dict[str, int]] = defaultdict(lambda: {"pass": 0, "fail": 0, "pending": 0})
    for line in lines:
        prof = next((p for p in profiles if p.user_id == line.student_user_id), None)
        if prof is None:
            continue
        prog = (prof.programme_code or "unknown").upper()
        norm = normalize_pass_fail(line.pass_fail)
        if norm == "pass":
            stats[prog]["pass"] += 1
        elif norm == "fail":
            stats[prog]["fail"] += 1
        else:
            stats[prog]["pending"] += 1
    return [
        ProgrammePerformanceRead(
            programme_code=prog,
            enrolled_students=len(rows),
            pass_count=stats[prog]["pass"],
            fail_count=stats[prog]["fail"],
            result_pending_count=stats[prog]["pending"],
            pass_percentage=pass_percentage(stats[prog]["pass"], stats[prog]["fail"]),
        )
        for prog, rows in sorted(by_prog.items())
    ]


async def performance_batches(scope: AccessScope, user: User, *, filters: PerformanceFilters) -> list[BatchPerformanceRead]:
    authorize(scope, Permission.DEPARTMENT_PERFORMANCE_READ)
    tenant_id, central_id, _, _, _ = await _context(scope, user)
    profiles = await _dept_profiles(tenant_id, central_id, filters)
    by_batch: dict[str, list[StudentProfile]] = defaultdict(list)
    for p in profiles:
        label = p.batch_label or "unspecified"
        by_batch[label].append(p)
    student_ids = [p.user_id for p in profiles]
    lines = await SemesterResultSubjectMark.find(_result_line_query(tenant_id, student_ids, filters)).to_list() if student_ids else []
    stats: dict[str, dict[str, int]] = defaultdict(lambda: {"pass": 0, "fail": 0})
    for line in lines:
        prof = next((p for p in profiles if p.user_id == line.student_user_id), None)
        if prof is None:
            continue
        batch = prof.batch_label or "unspecified"
        norm = normalize_pass_fail(line.pass_fail)
        if norm == "pass":
            stats[batch]["pass"] += 1
        elif norm == "fail":
            stats[batch]["fail"] += 1
    return [
        BatchPerformanceRead(
            batch_label=batch,
            enrolled_students=len(rows),
            pass_count=stats[batch]["pass"],
            fail_count=stats[batch]["fail"],
            pass_percentage=pass_percentage(stats[batch]["pass"], stats[batch]["fail"]),
        )
        for batch, rows in sorted(by_batch.items())
    ]


async def performance_subjects(scope: AccessScope, user: User, *, filters: PerformanceFilters) -> list[SubjectPerformanceRead]:
    authorize(scope, Permission.DEPARTMENT_PERFORMANCE_READ)
    tenant_id, central_id, _, course_codes, _ = await _context(scope, user)
    if filters.course_code:
        await assert_course_in_department(tenant_id, central_id, filters.course_code)
    codes = {filters.course_code.upper()} if filters.course_code else course_codes
    profiles = await _dept_profiles(tenant_id, central_id, filters)
    student_ids = [p.user_id for p in profiles]
    enroll_filters: dict = {
        "tenant_id": tenant_id,
        "student_user_id": {"$in": student_ids},
        "status": StudentEnrollmentStatus.ACTIVE.value,
    }
    if filters.academic_year_label:
        enroll_filters["academic_year_label"] = filters.academic_year_label
    if filters.semester_label:
        enroll_filters["semester_label"] = filters.semester_label
    enrollments = await StudentEnrollment.find(enroll_filters).to_list() if student_ids else []
    enrolled_by_course: dict[str, set[str]] = defaultdict(set)
    for e in enrollments:
        if e.course_code.upper() in codes:
            enrolled_by_course[e.course_code.upper()].add(str(e.student_user_id))
    lines = await SemesterResultSubjectMark.find(_result_line_query(tenant_id, student_ids, filters)).to_list() if student_ids else []
    stats: dict[str, dict[str, int]] = defaultdict(lambda: {"pass": 0, "fail": 0, "pending": 0, "published": 0})
    for line in lines:
        code = line.course_code.upper()
        if code not in codes:
            continue
        stats[code]["published"] += 1
        norm = normalize_pass_fail(line.pass_fail)
        if norm == "pass":
            stats[code]["pass"] += 1
        elif norm == "fail":
            stats[code]["fail"] += 1
        else:
            stats[code]["pending"] += 1
    result: list[SubjectPerformanceRead] = []
    for code in sorted(codes):
        enrolled = len(enrolled_by_course.get(code, set()))
        pending = max(enrolled - stats[code]["published"], 0) if enrolled else 0
        result.append(
            SubjectPerformanceRead(
                course_code=code,
                enrolled_students=enrolled,
                results_published=stats[code]["published"],
                pass_count=stats[code]["pass"],
                fail_count=stats[code]["fail"],
                result_pending_count=pending + stats[code]["pending"],
                pass_percentage=pass_percentage(stats[code]["pass"], stats[code]["fail"]),
            )
        )
    return result


async def performance_pass_fail(scope: AccessScope, user: User, *, filters: PerformanceFilters) -> PassFailSummaryRead:
    authorize(scope, Permission.DEPARTMENT_PERFORMANCE_READ)
    overview = await performance_overview(scope, user, filters=filters)
    student_ids_set: set[str] = set()
    passed_students: set[str] = set()
    failed_students: set[str] = set()
    tenant_id, central_id, _, _, _ = await _context(scope, user)
    profiles = await _dept_profiles(tenant_id, central_id, filters)
    student_ids = [p.user_id for p in profiles]
    lines = await SemesterResultSubjectMark.find(_result_line_query(tenant_id, student_ids, filters)).to_list() if student_ids else []
    for line in lines:
        sid = str(line.student_user_id)
        student_ids_set.add(sid)
        norm = normalize_pass_fail(line.pass_fail)
        if norm == "fail":
            failed_students.add(sid)
        elif norm == "pass":
            passed_students.add(sid)
    assessed = len(student_ids_set)
    return PassFailSummaryRead(
        meta=overview.meta,
        assessed_students=assessed,
        passed_students=len(passed_students),
        failed_students=len(failed_students),
        result_pending_students=overview.result_pending_count,
        result_withheld_students=overview.result_withheld_count,
        pass_percentage=pass_percentage(len(passed_students), len(failed_students)),
    )


async def performance_arrears(
    scope: AccessScope,
    user: User,
    *,
    filters: PerformanceFilters,
    pagination: Pagination,
) -> ArrearSummaryRead:
    authorize(scope, Permission.DEPARTMENT_PERFORMANCE_READ)
    tenant_id, central_id, _, _, _ = await _context(scope, user)
    profiles = await _dept_profiles(tenant_id, central_id, filters)
    profile_by_user = {p.user_id: p for p in profiles}
    student_ids = list(profile_by_user.keys())
    items: list[ArrearStudentRead] = []
    if student_ids:
        line_q = {"tenant_id": tenant_id, "student_user_id": {"$in": student_ids}, "published": True, "is_arrear": True}
        if filters.season_id:
            line_q["season_id"] = filters.season_id
        for line in await SemesterResultSubjectMark.find(line_q).sort("-published_at").to_list():
            prof = profile_by_user.get(line.student_user_id)
            items.append(
                ArrearStudentRead(
                    student_user_id=str(line.student_user_id),
                    roll_number=prof.roll_number if prof else None,
                    programme_code=prof.programme_code if prof else None,
                    course_code=line.course_code,
                    season_id=line.season_id,
                    attempt_number=line.attempt_number,
                    source_collection="semester_result_subject_marks",
                )
            )
        refs = await StudentArrearReference.find(
            {
                "tenant_id": tenant_id,
                "user_id": {"$in": student_ids},
                "backlog_status": BacklogStatus.PENDING,
            }
        ).to_list()
        existing = {(i.student_user_id, i.course_code) for i in items}
        for ref in refs:
            key = (str(ref.user_id), ref.course_code)
            if key in existing:
                continue
            prof = profile_by_user.get(ref.user_id)
            items.append(
                ArrearStudentRead(
                    student_user_id=str(ref.user_id),
                    roll_number=prof.roll_number if prof else None,
                    programme_code=prof.programme_code if prof else None,
                    course_code=ref.course_code,
                    season_id=ref.last_attempt_season_id,
                    attempt_number=None,
                    source_collection="student_arrear_references",
                )
            )
    total = len(items)
    page = items[pagination.offset : pagination.offset + pagination.limit]
    unique_students = len({i.student_user_id for i in items})
    return ArrearSummaryRead(
        meta=_meta(filters, basis="published_arrear_lines_and_student_arrear_references", count=len(profiles)),
        arrear_line_count=total,
        unique_students=unique_students,
        items=page,
    )


async def performance_progression(
    scope: AccessScope,
    user: User,
    *,
    filters: PerformanceFilters,
    pagination: Pagination,
) -> Page[ProgressionStudentRead]:
    authorize(scope, Permission.DEPARTMENT_PERFORMANCE_READ)
    tenant_id, central_id, _, _, _ = await _context(scope, user)
    profiles = await _dept_profiles(tenant_id, central_id, filters)
    profile_by_user = {p.user_id: p for p in profiles}
    student_ids = list(profile_by_user.keys())
    if not student_ids:
        return Page(items=[], total=0, limit=pagination.limit, offset=pagination.offset)
    rec_q: dict = {"tenant_id": tenant_id, "user_id": {"$in": student_ids}}
    if filters.academic_year_label:
        rec_q["academic_year_label"] = filters.academic_year_label
    if filters.semester_label:
        rec_q["semester_label"] = filters.semester_label
    query = StudentAcademicRecord.find(rec_q).sort("-updated_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    items: list[ProgressionStudentRead] = []
    for rec in rows:
        prof = profile_by_user.get(rec.user_id)
        items.append(
            ProgressionStudentRead(
                student_user_id=str(rec.user_id),
                roll_number=prof.roll_number if prof else None,
                programme_code=prof.programme_code if prof else None,
                academic_year_label=rec.academic_year_label,
                semester_label=rec.semester_label,
                progression_status=rec.progression_status,
                academic_standing=rec.academic_standing,
                credits_registered=rec.credits_registered,
                credits_earned=rec.credits_earned,
                cgpa=rec.cgpa,
                promotion_eligible=rec.promotion_eligible,
            )
        )
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def performance_students_requiring_support(
    scope: AccessScope,
    user: User,
    *,
    filters: PerformanceFilters,
    pagination: Pagination,
) -> StudentsRequiringSupportRead:
    authorize(scope, Permission.DEPARTMENT_PERFORMANCE_READ)
    tenant_id, central_id, _, _, _ = await _context(scope, user)
    enabled = sorted(DEFAULT_SUPPORT_INDICATORS)
    profiles = await _dept_profiles(tenant_id, central_id, filters)
    profile_by_user = {p.user_id: p for p in profiles}
    student_ids = list(profile_by_user.keys())
    flags_by_student: dict[str, list[SupportFlagRead]] = defaultdict(list)
    if "attendance_shortage" in DEFAULT_SUPPORT_INDICATORS and student_ids:
        try:
            shortages = await attendance_shortages(scope, user)
            for row in shortages:
                flags_by_student[row.student_user_id].append(
                    SupportFlagRead(
                        reason_code="attendance_shortage",
                        source_collection="attendance_records",
                        detail=f"percentage={row.percentage}",
                    )
                )
        except Exception:
            pass
    if "published_subject_failure" in DEFAULT_SUPPORT_INDICATORS and student_ids:
        fail_lines = await SemesterResultSubjectMark.find(
            {
                "tenant_id": tenant_id,
                "student_user_id": {"$in": student_ids},
                "published": True,
                "pass_fail": {"$in": ["fail", "FAIL", "failed"]},
            }
        ).limit(5000).to_list()
        for line in fail_lines:
            flags_by_student[str(line.student_user_id)].append(
                SupportFlagRead(
                    reason_code="published_subject_failure",
                    source_collection="semester_result_subject_marks",
                    detail=line.course_code,
                )
            )
    if "active_arrear" in DEFAULT_SUPPORT_INDICATORS and student_ids:
        refs = await StudentArrearReference.find(
            {"tenant_id": tenant_id, "user_id": {"$in": student_ids}, "backlog_status": BacklogStatus.PENDING}
        ).to_list()
        for ref in refs:
            flags_by_student[str(ref.user_id)].append(
                SupportFlagRead(
                    reason_code="active_arrear",
                    source_collection="student_arrear_references",
                    detail=ref.course_code,
                )
            )
    if "academic_standing" in DEFAULT_SUPPORT_INDICATORS and student_ids:
        recs = await StudentAcademicRecord.find(
            {
                "tenant_id": tenant_id,
                "user_id": {"$in": student_ids},
                "academic_standing": {
                    "$in": [AcademicStanding.PROBATION.value, AcademicStanding.SUSPENDED.value],
                },
            }
        ).to_list()
        for rec in recs:
            flags_by_student[str(rec.user_id)].append(
                SupportFlagRead(
                    reason_code="academic_standing",
                    source_collection="student_academic_records",
                    detail=rec.academic_standing.value,
                )
            )
    students_with_flags: list[StudentSupportRead] = []
    for uid, flags in flags_by_student.items():
        prof = profile_by_user.get(PydanticObjectId(uid))
        if prof is None:
            continue
        user_row = await User.get(PydanticObjectId(uid))
        students_with_flags.append(
            StudentSupportRead(
                student_user_id=uid,
                roll_number=prof.roll_number,
                display_name=user_row.full_name if user_row else None,
                programme_code=prof.programme_code,
                flags=flags,
            )
        )
    students_with_flags.sort(key=lambda s: s.student_user_id)
    total = len(students_with_flags)
    page = students_with_flags[pagination.offset : pagination.offset + pagination.limit]
    return StudentsRequiringSupportRead(
        meta=_meta(filters, basis="transparent_support_flags", count=len(profiles)),
        enabled_indicators=enabled,
        students=page,
    )


async def performance_trends(
    scope: AccessScope,
    user: User,
    *,
    season_ids: list[str],
) -> PerformanceTrendsRead:
    authorize(scope, Permission.DEPARTMENT_PERFORMANCE_READ)
    tenant_id, central_id, _, _, _ = await _context(scope, user)
    profiles = await StudentProfile.find({"tenant_id": tenant_id, "department_id": central_id}).limit(15000).to_list()
    student_ids = [p.user_id for p in profiles]
    periods: list[TrendPeriodRead] = []
    for sid in season_ids:
        if not sid.strip():
            continue
        filt = PerformanceFilters(season_id=sid.strip())
        lines = await SemesterResultSubjectMark.find(_result_line_query(tenant_id, student_ids, filt)).to_list() if student_ids else []
        pass_c = fail_c = 0
        if not lines and student_ids:
            periods.append(
                TrendPeriodRead(period_label=sid, data_available=False, enrolled_students=len(profiles))
            )
            continue
        for line in lines:
            norm = normalize_pass_fail(line.pass_fail)
            if norm == "pass":
                pass_c += 1
            elif norm == "fail":
                fail_c += 1
        periods.append(
            TrendPeriodRead(
                period_label=sid,
                data_available=bool(lines),
                pass_count=pass_c,
                fail_count=fail_c,
                pass_percentage=pass_percentage(pass_c, fail_c),
                enrolled_students=len(profiles),
            )
        )
    return PerformanceTrendsRead(
        meta=_meta(
            PerformanceFilters(),
            basis="semester_result_subject_marks.by_season",
            count=len(profiles),
        ),
        periods=periods,
    )


async def performance_follow_ups(
    scope: AccessScope,
    user: User,
    *,
    category: str | None,
    pagination: Pagination,
) -> Page[PerformanceFollowUpRead]:
    authorize(scope, Permission.DEPARTMENT_PERFORMANCE_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    filters = [
        Eq(DepartmentStudentFollowUp.tenant_id, tenant_id),
        Eq(DepartmentStudentFollowUp.central_department_id, central_id),
    ]
    if category:
        if category not in PERFORMANCE_FOLLOW_UP_CATEGORIES:
            raise AppError(code="VALIDATION_ERROR", message="Unknown performance follow-up category", status_code=422)
        filters.append(Eq(DepartmentStudentFollowUp.category, category))
    else:
        filters.append(In(DepartmentStudentFollowUp.category, list(PERFORMANCE_FOLLOW_UP_CATEGORIES)))
    query = DepartmentStudentFollowUp.find(*filters).sort("-created_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    items = [
        PerformanceFollowUpRead(
            follow_up_id=str(r.id),
            student_user_id=str(r.student_user_id),
            category=r.category,
            description=r.description,
            status=r.status.value,
            due_date=r.due_date,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)