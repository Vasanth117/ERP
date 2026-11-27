"""LMS course management and subject mapping (CA 15.02–03)."""

from __future__ import annotations

import math

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.academics.curriculum_models import CourseRecord
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.lms_admin_models import LmsCourseMapping
from app.modules.college_admin.lms_courses_shared import load_course_context, status_presentation
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    CommunicationChannelAlertBanner,
    InstitutionPolicyFilterOption,
    LmsCourseManagementPageRead,
    LmsCourseManagementRow,
    LmsSubjectCourseMappingPageRead,
    LmsSubjectMappingRow,
    PoliciesPagination,
)
from app.modules.faculty.enums import AssignmentStatus
from app.modules.faculty.models import FacultyAssignment

_COURSE_PAGE_SIZE = 4
_MAPPING_PAGE_SIZE = 3

_STATUS_FILTERS = [
    ("", "All statuses"),
    ("published", "Published"),
    ("draft", "Draft"),
]


def _paginate(rows: list, page: int, page_size: int):
    total = len(rows)
    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    offset = (page - 1) * page_size
    paged = rows[offset : offset + page_size]
    total_pages = math.ceil(total / page_size) if total else 0
    showing_end = min(total, offset + len(paged))
    return paged, total, total_pages, f"Showing {showing_end:,} of {total:,}", f"{showing_end:,} of {total:,}"


async def get_lms_course_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _COURSE_PAGE_SIZE,
    search: str | None = None,
    department: str | None = None,
    status: str | None = None,
) -> LmsCourseManagementPageRead:
    authorize(scope, Permission.LMS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    ctx = await load_course_context(tenant_id)

    needle = (search or "").strip().lower()
    dept_key = (department or "").strip()
    status_key = (status or "").strip().lower()

    dept_options = [InstitutionPolicyFilterOption(value="", label="All departments")]
    seen_depts: set[str] = set()
    for course in ctx["courses"]:
        if course.department_id:
            oid = str(course.department_id)
            if oid not in seen_depts:
                seen_depts.add(oid)
                dept_options.append(
                    InstitutionPolicyFilterOption(
                        value=oid,
                        label=ctx["dept_by_id"].get(course.department_id, oid),
                    )
                )

    rows: list[LmsCourseManagementRow] = []
    for course in ctx["courses"]:
        code = course.course_code.upper()
        mapping = ctx["mappings_by_code"].get(code)
        published = mapping.published if mapping else None
        status_label, status_tone = status_presentation(
            published=published,
            configuration_status=course.configuration_status,
        )
        st_key = "published" if status_label == "Published" else "draft"
        if dept_key and str(course.department_id or "") != dept_key:
            continue
        if status_key and st_key != status_key:
            continue
        if needle and needle not in course.name.lower() and needle not in code.lower():
            continue
        rows.append(
            LmsCourseManagementRow(
                row_key=code,
                course_label=course.name,
                course_code=code,
                department_label=ctx["dept_by_id"].get(course.department_id, "—") if course.department_id else "—",
                faculty_label=ctx["faculty_label"](code),
                students_count=len(ctx["students_by_code"].get(code, set())),
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/lms/course-management?course_code={code}",
            )
        )

    if not rows and not ctx["courses"]:
        for mapping in ctx["mappings"]:
            code = mapping.course_code.upper()
            status_label, status_tone = status_presentation(published=mapping.published)
            st_key = "published" if status_label == "Published" else "draft"
            if status_key and st_key != status_key:
                continue
            label = ctx["title_by_code"].get(code, mapping.course_id or code)
            if needle and needle not in label.lower() and needle not in code.lower():
                continue
            if dept_key and str(mapping.department_id or "") != dept_key:
                continue
            rows.append(
                LmsCourseManagementRow(
                    row_key=code,
                    course_label=label,
                    course_code=code,
                    department_label=ctx["dept_by_id"].get(mapping.department_id, "—") if mapping.department_id else "—",
                    faculty_label=ctx["faculty_label"](code),
                    students_count=len(ctx["students_by_code"].get(code, set())),
                    status_label=status_label,
                    status_tone=status_tone,
                    detail_href=f"/college-admin/lms/course-management?course_code={code}",
                )
            )

    paged, total, total_pages, footer, _ = _paginate(rows, page, page_size)

    return LmsCourseManagementPageRead(
        page_title="Course Management",
        page_subtitle="Courses, owners and publishing",
        primary_action_label="Create course",
        primary_action_href="/college-admin/academics/course-configuration?mode=create",
        search_placeholder="Search course or code",
        department_filter_label="All departments",
        status_filter_label="All statuses",
        department_options=dept_options,
        status_options=[InstitutionPolicyFilterOption(value=v, label=l) for v, l in _STATUS_FILTERS],
        courses_section_title="Courses",
        table_headers=["Course", "Code", "Department", "Faculty", "Students", "Status"],
        course_rows=paged,
        empty_table_message="No courses match your filters.",
        showing_label=footer,
        count_footer_label=footer,
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


def _mapping_status(mapping: LmsCourseMapping | None) -> tuple[str, str]:
    if mapping and (mapping.lms_course_key or mapping.published):
        return "Mapped", "success"
    return "Unmapped", "warning"


async def get_lms_subject_course_mapping_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _MAPPING_PAGE_SIZE,
) -> LmsSubjectCourseMappingPageRead:
    authorize(scope, Permission.LMS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    ctx = await load_course_context(tenant_id)

    active_assignments = [
        a for a in ctx["faculty_assignments"] if a.status == AssignmentStatus.ACTIVE and a.course_code
    ]
    active_assignments.sort(key=lambda a: (a.subject_name or a.course_name or "", a.section or ""))

    rows: list[LmsSubjectMappingRow] = []
    unmapped = 0
    for fa in active_assignments:
        code = fa.course_code.upper()
        mapping = ctx["mappings_by_code"].get(code)
        status_label, status_tone = _mapping_status(mapping)
        if status_label == "Unmapped":
            unmapped += 1
        user = ctx["faculty_users"].get(str(fa.user_id))
        faculty_label = user.full_name if user and user.full_name else "—"
        lms_label = mapping.lms_course_key if mapping and mapping.lms_course_key else "—"
        rows.append(
            LmsSubjectMappingRow(
                row_key=f"{code}:{fa.section}:{fa.user_id}",
                subject_label=fa.subject_name or fa.course_name or code,
                section_label=fa.section or "—",
                faculty_label=faculty_label,
                lms_course_label=lms_label,
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/lms/subject-course-mapping?course_code={code}",
            )
        )

    if not rows:
        for course in ctx["courses"]:
            code = course.course_code.upper()
            mapping = ctx["mappings_by_code"].get(code)
            status_label, status_tone = _mapping_status(mapping)
            if status_label == "Unmapped":
                unmapped += 1
            rows.append(
                LmsSubjectMappingRow(
                    row_key=code,
                    subject_label=course.name,
                    section_label=ctx["section_by_code"].get(code, "—"),
                    faculty_label=ctx["faculty_label"](code),
                    lms_course_label=mapping.lms_course_key if mapping else "—",
                    status_label=status_label,
                    status_tone=status_tone,
                    detail_href=f"/college-admin/lms/subject-course-mapping?course_code={code}",
                )
            )

    paged, total, total_pages, footer, short_footer = _paginate(rows, page, page_size)

    alert: CommunicationChannelAlertBanner | None = None
    if unmapped:
        alert = CommunicationChannelAlertBanner(
            tone="warning",
            message=f"{unmapped:,} subjects have no LMS course",
            link_label="Create or map courses so students can see content for these subjects.",
            link_href="/college-admin/lms/course-management",
        )

    return LmsSubjectCourseMappingPageRead(
        page_title="Subject & Course Mapping",
        page_subtitle="Map subjects to LMS courses",
        auto_map_action_label="Auto map",
        save_mapping_action_label="Save mapping",
        save_mapping_enabled=unmapped > 0,
        alert_banner=alert,
        mapping_section_title="Mapping",
        table_headers=["Subject", "Section", "Faculty", "LMS course", "Status"],
        mapping_rows=paged,
        empty_table_message="No subject mappings to show yet.",
        count_footer_label=short_footer,
        showing_label=footer,
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


async def auto_map_lms_subject_courses(scope: AccessScope) -> dict:
    authorize(scope, Permission.LMS_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    ctx = await load_course_context(tenant_id)
    created = 0
    for fa in ctx["faculty_assignments"]:
        if fa.status != AssignmentStatus.ACTIVE or not fa.course_code:
            continue
        code = fa.course_code.strip().upper()
        if code in ctx["mappings_by_code"]:
            continue
        course = next((c for c in ctx["courses"] if c.course_code.upper() == code), None)
        doc = LmsCourseMapping(
            tenant_id=tenant_id,
            course_id=fa.course_name or (course.name if course else code),
            course_code=code,
            lms_course_key=code.replace("_", "-"),
            department_id=course.department_id if course else None,
            published=False,
            actor_id=scope.user_id,
        )
        await doc.insert()
        ctx["mappings_by_code"][code] = doc
        created += 1
    return {"created": created}


async def save_lms_subject_mappings(scope: AccessScope) -> dict:
    authorize(scope, Permission.LMS_ADMIN_MANAGE)
    result = await auto_map_lms_subject_courses(scope)
    tenant_id = require_college_tenant_scope(scope)
    updated = 0
    mappings = await LmsCourseMapping.find(Eq(LmsCourseMapping.tenant_id, tenant_id)).to_list()
    for mapping in mappings:
        if not mapping.lms_course_key:
            mapping.lms_course_key = mapping.course_code.replace("_", "-")
            mapping.updated_at = utcnow()
            await mapping.save()
            updated += 1
    return {"created": result["created"], "updated": updated}