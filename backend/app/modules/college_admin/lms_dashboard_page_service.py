"""LMS administration overview dashboard (CA 15.01)."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import timedelta

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.common.ids import to_object_id
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.lms_admin_models import LmsCourseMapping
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    LmsDashboardCompletionBar,
    LmsDashboardCourseRow,
    LmsDashboardPageRead,
    PoliciesPagination,
    UserDashboardKpi,
)
from app.modules.lms.enums import LmsAssignmentStatus, MaterialPublishState
from app.modules.lms.models import CourseAssignment, LearningMaterial
from app.modules.students.student_lms_models import StudentLearningProgress

_PAGE_SIZE = 4
_TABLE_HEADERS = ["Course", "Code", "Department", "Faculty", "Students", "Status"]
_COMPLETION_TONES = ("success", "info", "warning", "muted")

_reader = OperationalDataReader()


def _status_presentation(published: bool) -> tuple[str, str]:
    if published:
        return "Published", "success"
    return "Draft", "warning"


def _course_label(mapping: LmsCourseMapping, title_by_code: dict[str, str]) -> str:
    if mapping.course_id and not mapping.course_id.isdigit():
        return mapping.course_id
    return title_by_code.get(mapping.course_code, mapping.course_id or mapping.course_code)


async def get_lms_dashboard_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> LmsDashboardPageRead:
    authorize(scope, Permission.LMS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    week_ago = now - timedelta(days=7)

    ay_label, sem_label = await _reader.current_academic_term(tenant_id)
    ay_label = ay_label or "—"
    sem_label = sem_label or "Current term"
    page_subtitle = f"Learning activity · {sem_label} {ay_label}".replace("  ", " ").strip(" ·")

    mappings = await LmsCourseMapping.find(Eq(LmsCourseMapping.tenant_id, tenant_id)).sort("-updated_at").to_list()
    materials = await LearningMaterial.find(Eq(LearningMaterial.tenant_id, tenant_id)).to_list()
    assignments = await CourseAssignment.find(Eq(CourseAssignment.tenant_id, tenant_id)).to_list()
    progress_rows = await StudentLearningProgress.find(Eq(StudentLearningProgress.tenant_id, tenant_id)).to_list()

    title_by_code: dict[str, str] = {}
    faculty_by_code: dict[str, str] = {}
    for mat in materials:
        if mat.title and mat.course_code:
            title_by_code.setdefault(mat.course_code, mat.title)
        if mat.faculty_user_id:
            faculty_by_code.setdefault(mat.course_code, str(mat.faculty_user_id))
    for assign in assignments:
        if assign.title and assign.course_code and assign.course_code not in title_by_code:
            title_by_code[assign.course_code] = assign.title
        if assign.faculty_user_id:
            faculty_by_code.setdefault(assign.course_code, str(assign.faculty_user_id))

    students_by_code: dict[str, set] = defaultdict(set)
    for row in progress_rows:
        students_by_code[row.course_code].add(row.user_id)

    active_courses = len({m.course_code for m in mappings if m.published}) or len(mappings)
    materials_total = len(materials)
    active_learners = len({p.user_id for p in progress_rows if p.last_activity_at and p.last_activity_at >= week_ago})
    total_learners = len({p.user_id for p in progress_rows})
    learner_pct = (active_learners / total_learners * 100) if total_learners else 0.0
    awaiting_review = sum(1 for m in materials if m.publish_state == MaterialPublishState.DRAFT) + sum(
        1 for a in assignments if a.status == LmsAssignmentStatus.DRAFT
    )

    dept_ids = {m.department_id for m in mappings if m.department_id}
    dept_by_id: dict = {}
    if dept_ids:
        for dept in await InstitutionDepartment.find(In(InstitutionDepartment.id, list(dept_ids))).to_list():
            dept_by_id[dept.id] = dept.name or "—"

    faculty_oid_ids = []
    for raw in {faculty_by_code[c] for c in faculty_by_code if faculty_by_code.get(c)}:
        faculty_oid_ids.append(to_object_id(raw, "faculty_user_id"))
    faculty_users: dict[str, User] = {}
    if faculty_oid_ids:
        for user in await User.find(In(User.id, faculty_oid_ids)).to_list():
            faculty_users[str(user.id)] = user

    course_rows: list[LmsDashboardCourseRow] = []
    for mapping in mappings:
        code = mapping.course_code
        faculty_id = faculty_by_code.get(code)
        user = faculty_users.get(faculty_id) if faculty_id else None
        faculty_label = user.full_name if user and user.full_name else "—"
        status_label, status_tone = _status_presentation(mapping.published)
        course_rows.append(
            LmsDashboardCourseRow(
                row_key=code,
                course_label=_course_label(mapping, title_by_code),
                course_code=code,
                department_label=dept_by_id.get(mapping.department_id, "—") if mapping.department_id else "—",
                faculty_label=faculty_label,
                students_count=len(students_by_code.get(code, set())),
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/lms/course-management?course_code={code}",
            )
        )

    total_courses = len(course_rows)
    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    offset = (page - 1) * page_size
    paged = course_rows[offset : offset + page_size]
    total_pages = math.ceil(total_courses / page_size) if total_courses else 0
    showing_end = min(total_courses, offset + len(paged))
    showing_label = f"Showing {showing_end:,} of {total_courses:,}"

    dept_codes: dict[str, list[str]] = defaultdict(list)
    for m in mappings:
        if m.department_id:
            dept_codes[str(m.department_id)].append(m.course_code)

    completion_bars: list[LmsDashboardCompletionBar] = []
    tone_idx = 0
    for dept_id, codes in sorted(dept_codes.items(), key=lambda x: dept_by_id.get(x[0], "")):
        progresses = [p for p in progress_rows if p.course_code in codes]
        if progresses:
            scores = []
            for p in progresses:
                score = min(100, p.materials_viewed * 4 + p.assignments_submitted * 12 + p.quizzes_completed * 8)
                scores.append(score)
            pct = int(sum(scores) / len(scores))
        else:
            pct = 0
        completion_bars.append(
            LmsDashboardCompletionBar(
                department_label=dept_by_id.get(dept_id, "Department"),
                completion_percent=pct,
                tone=_COMPLETION_TONES[tone_idx % len(_COMPLETION_TONES)],
            )
        )
        tone_idx += 1
    completion_bars.sort(key=lambda b: b.completion_percent, reverse=True)

    return LmsDashboardPageRead(
        page_title="LMS Dashboard",
        page_subtitle=page_subtitle,
        export_label="Export",
        kpis=[
            UserDashboardKpi(
                key="active_courses",
                label="Active courses",
                value=f"{active_courses:,}",
                hint_line="",
                hint_tone="muted",
            ),
            UserDashboardKpi(
                key="materials",
                label="Learning materials",
                value=f"{materials_total:,}",
                hint_line="",
                hint_tone="muted",
            ),
            UserDashboardKpi(
                key="active_learners",
                label="Active learners (7 days)",
                value=f"{active_learners:,}",
                hint_line=f"{learner_pct:.1f}%" if total_learners else "",
                hint_tone="success" if learner_pct >= 50 else "muted",
            ),
            UserDashboardKpi(
                key="review",
                label="Content awaiting review",
                value=f"{awaiting_review:,}",
                hint_line="",
                hint_tone="warning" if awaiting_review else "muted",
            ),
        ],
        courses_section_title="Courses",
        table_headers=_TABLE_HEADERS,
        course_rows=paged,
        empty_table_message="No LMS courses configured yet.",
        completion_section_title="Course completion",
        completion_bars=completion_bars,
        empty_completion_message="No completion data for departments yet.",
        showing_label=showing_label,
        count_footer_label=showing_label,
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total_courses,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        generated_at=now,
    )