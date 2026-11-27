"""LMS content administration pages (CA 15.04–05)."""

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
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.lms_admin_models import LmsPublishingPolicy
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    LmsLearningMaterialManagementPageRead,
    LmsLearningMaterialRow,
    LmsVideoLectureManagementPageRead,
    LmsVideoLectureRow,
    PoliciesPagination,
    UserDashboardKpi,
)
from app.modules.lms.enums import MaterialPublishState
from app.modules.lms.models import LearningMaterial
from app.modules.students.student_lms_models import StudentMaterialAccessLog

_MATERIAL_PAGE_SIZE = 3
_VIDEO_PAGE_SIZE = 3
_VIDEO_MATERIAL_TYPES = frozenset({"video", "recording"})


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


def _type_label(doc: LearningMaterial) -> str:
    mime = (doc.mime_type or "").lower()
    if "pdf" in mime:
        return "PDF"
    if doc.material_type == "link":
        return "Link"
    if doc.material_type in _VIDEO_MATERIAL_TYPES:
        return "Video"
    name = (doc.file_name or "").rsplit(".", 1)
    if len(name) == 2 and name[1]:
        return name[1].upper()
    return (doc.material_type or "Document").replace("_", " ").title()


def _date_label(created_at) -> str:
    return created_at.strftime("%d %b")


async def _publishing_requires_approval(tenant_id) -> bool:
    doc = await LmsPublishingPolicy.find_one(Eq(LmsPublishingPolicy.tenant_id, tenant_id))
    return bool(doc and doc.material_requires_approval)


async def _faculty_names(tenant_id, user_ids: set) -> dict[str, str]:
    if not user_ids:
        return {}
    oids = [to_object_id(uid) for uid in user_ids if uid]
    users = await User.find(In(User.id, oids)).to_list()
    return {str(u.id): (u.full_name or u.email or str(u.id)) for u in users}


def _material_status(doc: LearningMaterial, *, requires_approval: bool) -> tuple[str, str]:
    if doc.publish_state == MaterialPublishState.PUBLISHED:
        return "Published", "success"
    if requires_approval:
        return "In review", "warning"
    return "Draft", "warning"


def _video_status(doc: LearningMaterial) -> tuple[str, str]:
    meta = doc.metadata or {}
    processing = str(meta.get("processing_status") or "").lower()
    if processing in {"processing", "pending", "queued", "transcoding"}:
        return "Processing", "info"
    if processing == "failed":
        return "Failed", "error"
    if doc.publish_state == MaterialPublishState.PUBLISHED:
        return "Published", "success"
    if doc.material_type in _VIDEO_MATERIAL_TYPES and doc.publish_state == MaterialPublishState.DRAFT:
        return "Processing", "info"
    return "Draft", "muted"


def _duration_label(doc: LearningMaterial) -> str:
    meta = doc.metadata or {}
    seconds = meta.get("duration_seconds")
    if seconds is None and meta.get("duration_minutes") is not None:
        seconds = int(meta["duration_minutes"]) * 60
    if seconds is None:
        return "—"
    try:
        total_min = max(0, int(seconds) // 60)
    except (TypeError, ValueError):
        return "—"
    if total_min < 60:
        return f"{total_min} min"
    hours = total_min // 60
    mins = total_min % 60
    if mins:
        return f"{hours} h {mins} min"
    return f"{hours} h"


async def _view_counts(tenant_id, material_ids: list) -> tuple[dict[str, int], int]:
    if not material_ids:
        return {}, 0
    logs = await StudentMaterialAccessLog.find(
        Eq(StudentMaterialAccessLog.tenant_id, tenant_id),
        In(StudentMaterialAccessLog.material_id, material_ids),
    ).to_list()
    week_ago = utcnow() - timedelta(days=7)
    by_material: dict[str, int] = defaultdict(int)
    week_total = 0
    for log in logs:
        mid = str(log.material_id)
        by_material[mid] += 1
        if log.accessed_at and log.accessed_at >= week_ago:
            week_total += 1
    return dict(by_material), week_total


async def get_lms_learning_material_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _MATERIAL_PAGE_SIZE,
) -> LmsLearningMaterialManagementPageRead:
    authorize(scope, Permission.LMS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    requires_approval = await _publishing_requires_approval(tenant_id)

    docs = await LearningMaterial.find(Eq(LearningMaterial.tenant_id, tenant_id)).sort("-created_at").to_list()
    docs = [d for d in docs if (d.material_type or "document") not in _VIDEO_MATERIAL_TYPES]

    faculty_ids = {str(d.faculty_user_id) for d in docs if d.faculty_user_id}
    faculty_by_id = await _faculty_names(tenant_id, faculty_ids)

    rows: list[LmsLearningMaterialRow] = []
    for doc in docs:
        fid = str(doc.faculty_user_id) if doc.faculty_user_id else ""
        status_label, status_tone = _material_status(doc, requires_approval=requires_approval)
        rows.append(
            LmsLearningMaterialRow(
                row_key=str(doc.id),
                material_label=doc.title,
                course_code=doc.course_code.upper() if doc.course_code else "—",
                type_label=_type_label(doc),
                uploaded_by_label=faculty_by_id.get(fid, "—"),
                date_label=_date_label(doc.created_at),
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/lms/learning-material-management?material_id={doc.id}",
            )
        )

    paged, total, total_pages, footer, _ = _paginate(rows, page, page_size)

    return LmsLearningMaterialManagementPageRead(
        page_title="Learning Material Management",
        page_subtitle="Documents, slides and links",
        primary_action_label="Upload material",
        primary_action_href="/college-admin/lms/faculty-content-management?focus=upload-material",
        materials_section_title="Learning materials",
        table_headers=["Material", "Course", "Type", "Uploaded by", "Date", "Status"],
        material_rows=paged,
        empty_table_message="No learning materials to show yet.",
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


async def get_lms_video_lecture_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _VIDEO_PAGE_SIZE,
) -> LmsVideoLectureManagementPageRead:
    authorize(scope, Permission.LMS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    docs = await LearningMaterial.find(Eq(LearningMaterial.tenant_id, tenant_id)).sort("-created_at").to_list()
    videos = [d for d in docs if (d.material_type or "") in _VIDEO_MATERIAL_TYPES]

    material_ids = [d.id for d in videos]
    views_by_id, views_week = await _view_counts(tenant_id, material_ids)

    total_duration_sec = 0
    processing_count = 0
    for doc in videos:
        meta = doc.metadata or {}
        seconds = meta.get("duration_seconds")
        if seconds is None and meta.get("duration_minutes") is not None:
            try:
                seconds = int(meta["duration_minutes"]) * 60
            except (TypeError, ValueError):
                seconds = None
        if seconds is not None:
            try:
                total_duration_sec += int(seconds)
            except (TypeError, ValueError):
                pass
        status_label, _ = _video_status(doc)
        if status_label == "Processing":
            processing_count += 1

    total_hours = total_duration_sec // 3600
    duration_value = f"{total_hours:,} h" if total_hours else "0 h"

    rows: list[LmsVideoLectureRow] = []
    for doc in videos:
        status_label, status_tone = _video_status(doc)
        mid = str(doc.id)
        views = views_by_id.get(mid, 0)
        rows.append(
            LmsVideoLectureRow(
                row_key=mid,
                lecture_label=doc.title,
                course_code=doc.course_code.upper() if doc.course_code else "—",
                length_label=_duration_label(doc),
                views_label=f"{views:,}" if views else "—",
                uploaded_label=_date_label(doc.created_at),
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/lms/video-lecture-management?material_id={doc.id}",
            )
        )

    paged, total, total_pages, _, short_footer = _paginate(rows, page, page_size)

    return LmsVideoLectureManagementPageRead(
        page_title="Video Lecture Management",
        page_subtitle="Recorded lectures and streaming",
        primary_action_label="Add video",
        primary_action_href="/college-admin/lms/faculty-content-management?focus=upload-video",
        kpis=[
            UserDashboardKpi(
                key="videos",
                label="Videos",
                value=f"{len(videos):,}",
                hint_line="",
                hint_tone="muted",
            ),
            UserDashboardKpi(
                key="duration",
                label="Total duration",
                value=duration_value,
                hint_line="",
                hint_tone="muted",
            ),
            UserDashboardKpi(
                key="views_week",
                label="Views this week",
                value=f"{views_week:,}",
                hint_line="",
                hint_tone="muted",
            ),
            UserDashboardKpi(
                key="processing",
                label="Processing",
                value=f"{processing_count:,}",
                hint_line="",
                hint_tone="muted",
            ),
        ],
        videos_section_title="Videos",
        table_headers=["Lecture", "Course", "Length", "Views", "Uploaded", "Status"],
        video_rows=paged,
        empty_table_message="No video lectures to show yet.",
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