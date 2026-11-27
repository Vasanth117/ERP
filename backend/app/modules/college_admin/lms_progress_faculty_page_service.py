"""LMS progress and faculty content pages (CA 15.09–10)."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import timedelta

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyRecord
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    LmsFacultyContentManagementPageRead,
    LmsFacultyContentRow,
    LmsStudentLearningProgressPageRead,
    LmsStudentLearningProgressRow,
    PoliciesPagination,
    UserDashboardKpi,
)
from app.modules.college_admin.student_admin_models import StudentRecord
from app.modules.lms.enums import MaterialPublishState
from app.modules.lms.models import LearningMaterial
from app.modules.students.student_lms_models import StudentLearningProgress

_PAGE_SIZE = 3
_VIDEO_TYPES = frozenset({"video", "recording"})
_AT_RISK_THRESHOLD = 50


def _paginate(rows: list, page: int, page_size: int):
    total = len(rows)
    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    offset = (page - 1) * page_size
    paged = rows[offset : offset + page_size]
    total_pages = math.ceil(total / page_size) if total else 0
    showing_end = min(total, offset + len(paged))
    footer = f"Showing {showing_end:,} of {total:,}"
    short_footer = f"{showing_end:,} of {total:,}"
    return paged, total, total_pages, footer, short_footer


def _course_completion(row: StudentLearningProgress) -> int:
    return min(100, row.materials_viewed * 4 + row.assignments_submitted * 12 + row.quizzes_completed * 8)


def _last_active_label(last_at, now) -> str:
    if not last_at:
        return "—"
    day = last_at.date()
    today = now.date()
    delta = (today - day).days
    if delta <= 0:
        return "Today"
    if delta == 1:
        return "Yesterday"
    return last_at.strftime("%d %b")


def _register_number(record: StudentRecord | None) -> str:
    if not record:
        return "—"
    for candidate in (record.roll_number, record.student_id):
        if candidate:
            return str(candidate)
    return "—"


async def get_lms_student_learning_progress_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> LmsStudentLearningProgressPageRead:
    authorize(scope, Permission.LMS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    week_ago = now - timedelta(days=7)
    stale_cutoff = now - timedelta(days=14)

    progress_rows = await StudentLearningProgress.find(Eq(StudentLearningProgress.tenant_id, tenant_id)).to_list()
    records = await StudentRecord.find(Eq(StudentRecord.tenant_id, tenant_id)).to_list()
    record_by_user = {str(r.user_id): r for r in records if r.user_id}

    by_user: dict[str, dict] = {}
    for row in progress_rows:
        uid = str(row.user_id)
        bucket = by_user.setdefault(
            uid,
            {"completion_scores": [], "last_at": None},
        )
        bucket["completion_scores"].append(_course_completion(row))
        if row.last_activity_at and (bucket["last_at"] is None or row.last_activity_at > bucket["last_at"]):
            bucket["last_at"] = row.last_activity_at

    user_ids = {to_object_id(uid) for uid in by_user}
    users: dict[str, User] = {}
    if user_ids:
        for user in await User.find(In(User.id, list(user_ids))).to_list():
            users[str(user.id)] = user

    learner_rows: list[LmsStudentLearningProgressRow] = []
    completion_values: list[int] = []
    at_risk = 0
    active_week = 0
    stale_login = 0

    for uid, bucket in by_user.items():
        scores = bucket["completion_scores"]
        completion = int(round(sum(scores) / len(scores))) if scores else 0
        completion_values.append(completion)
        last_at = bucket["last_at"]
        if completion < _AT_RISK_THRESHOLD:
            at_risk += 1
            status_label, status_tone = "At risk", "error"
        else:
            status_label, status_tone = "On track", "success"
        if last_at and last_at >= week_ago:
            active_week += 1
        if last_at is None or last_at < stale_cutoff:
            stale_login += 1
        user = users.get(uid)
        record = record_by_user.get(uid)
        label = (user.full_name if user and user.full_name else None) or "—"
        learner_rows.append(
            LmsStudentLearningProgressRow(
                row_key=uid,
                student_label=label,
                register_number=_register_number(record),
                completion_percent=completion,
                last_active_label=_last_active_label(last_at, now),
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/lms/student-learning-progress?user_id={uid}",
            )
        )

    learner_rows.sort(key=lambda r: (-r.completion_percent, r.student_label))

    avg_completion = int(round(sum(completion_values) / len(completion_values))) if completion_values else 0
    total_learners = max(len(records), len(learner_rows))

    paged, _, total_pages, _, _ = _paginate(learner_rows, page, page_size)
    showing_end = min(len(learner_rows), (page - 1) * page_size + len(paged))
    short_footer = f"{showing_end:,} of {total_learners:,}" if total_learners else "0 of 0"

    return LmsStudentLearningProgressPageRead(
        page_title="Student Learning Progress",
        page_subtitle="Engagement and completion",
        export_label="Export",
        learners_section_title="Learners",
        table_headers=["Student", "Register no.", "Completion", "Last active", "Status"],
        kpis=[
            UserDashboardKpi(
                key="avg_completion",
                label="Average completion",
                value=f"{avg_completion}%",
                hint_line="",
                hint_tone="muted",
            ),
            UserDashboardKpi(
                key="at_risk",
                label="At risk",
                value=f"{at_risk:,}",
                hint_line="Low engagement",
                hint_tone="error",
            ),
            UserDashboardKpi(
                key="active_week",
                label="Active this week",
                value=f"{active_week:,}",
                hint_line="",
                hint_tone="muted",
            ),
            UserDashboardKpi(
                key="stale_login",
                label="Not logged in 14 days",
                value=f"{stale_login:,}",
                hint_line="",
                hint_tone="muted",
            ),
        ],
        learner_rows=paged,
        empty_table_message="No learner progress to show yet.",
        count_footer_label=short_footer,
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=len(learner_rows),
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        generated_at=now,
    )


async def get_lms_faculty_content_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> LmsFacultyContentManagementPageRead:
    authorize(scope, Permission.LMS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    materials = await LearningMaterial.find(Eq(LearningMaterial.tenant_id, tenant_id)).to_list()
    faculty_ids = {m.faculty_user_id for m in materials if m.faculty_user_id}

    dept_by_id: dict = {}
    dept_ids: set = set()
    employees = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    faculty_records = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).to_list()
    emp_by_user = {e.user_id: e for e in employees}
    faculty_by_user = {f.user_id: f for f in faculty_records}
    for e in employees:
        if e.department_id:
            dept_ids.add(e.department_id)
    for f in faculty_records:
        if f.department_id:
            dept_ids.add(f.department_id)
    if dept_ids:
        for dept in await InstitutionDepartment.find(In(InstitutionDepartment.id, list(dept_ids))).to_list():
            dept_by_id[dept.id] = dept.name or "—"

    stats: dict[str, dict[str, int]] = defaultdict(lambda: {"materials": 0, "videos": 0, "pending": 0})
    for doc in materials:
        fid = str(doc.faculty_user_id)
        if (doc.material_type or "") in _VIDEO_TYPES:
            stats[fid]["videos"] += 1
        else:
            stats[fid]["materials"] += 1
        if doc.publish_state == MaterialPublishState.DRAFT:
            stats[fid]["pending"] += 1
        faculty_ids.add(doc.faculty_user_id)

    users: dict[str, User] = {}
    if faculty_ids:
        for user in await User.find(In(User.id, list(faculty_ids))).to_list():
            users[str(user.id)] = user

    rows: list[LmsFacultyContentRow] = []
    pending_total = 0
    for fid in faculty_ids:
        fid_str = str(fid)
        bucket = stats[fid_str]
        pending_total += bucket["pending"]
        user = users.get(fid_str)
        emp = emp_by_user.get(fid) or faculty_by_user.get(fid)
        dept_id = None
        if isinstance(emp, EmployeeRecord):
            dept_id = emp.department_id
        elif isinstance(emp, FacultyRecord):
            dept_id = emp.department_id
        dept_label = dept_by_id.get(dept_id, "—") if dept_id else "—"
        rows.append(
            LmsFacultyContentRow(
                row_key=fid_str,
                faculty_label=(user.full_name if user and user.full_name else None) or "—",
                department_label=dept_label,
                materials_count=bucket["materials"],
                videos_count=bucket["videos"],
                pending_review_count=bucket["pending"],
                detail_href=f"/college-admin/lms/faculty-content-management?faculty_user_id={fid_str}",
            )
        )

    rows.sort(key=lambda r: (-r.pending_review_count, -r.materials_count, r.faculty_label))

    paged, total, total_pages, _, short_footer = _paginate(rows, page, page_size)

    return LmsFacultyContentManagementPageRead(
        page_title="Faculty Content Management",
        page_subtitle="Faculty uploads and approvals",
        approve_selected_action_label="Approve selected",
        approve_selected_enabled=pending_total > 0,
        faculty_section_title="Faculty content",
        table_headers=["Faculty", "Department", "Materials", "Videos", "Pending review"],
        faculty_rows=paged,
        empty_table_message="No faculty content to show yet.",
        count_footer_label=short_footer,
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        generated_at=now,
    )


async def approve_selected_faculty_content(scope: AccessScope) -> dict:
    authorize(scope, Permission.LMS_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    docs = await LearningMaterial.find(
        Eq(LearningMaterial.tenant_id, tenant_id),
        Eq(LearningMaterial.publish_state, MaterialPublishState.DRAFT),
    ).to_list()
    approved = 0
    for doc in docs:
        doc.publish_state = MaterialPublishState.PUBLISHED
        doc.updated_at = utcnow()
        await doc.save()
        approved += 1
    return {"approved": approved}