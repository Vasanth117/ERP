"""LMS unit & chapter management page (CA 15.06)."""

from __future__ import annotations

from collections import defaultdict

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.academics.curriculum_models import CourseRecord, SyllabusRecord
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    LmsChapterRow,
    LmsUnitChapterCourseOption,
    LmsUnitChapterManagementPageRead,
    LmsUnitChapterRow,
)
from app.modules.lms.enums import MaterialPublishState
from app.modules.lms.models import LearningMaterial


def _chapter_key_from_material(doc: LearningMaterial) -> str | None:
    meta = doc.metadata or {}
    for key in ("chapter", "chapter_title", "topic", "topic_title"):
        raw = meta.get(key)
        if raw:
            text = str(raw).strip()
            if text:
                return text
    return None


def _materials_count_label(count: int) -> str:
    if count == 1:
        return "1 material"
    return f"{count:,} materials"


def _chapter_count_label(count: int) -> str:
    if count == 1:
        return "1 chapter"
    return f"{count:,} chapters"


def _unit_status(materials: list[LearningMaterial]) -> tuple[str, str]:
    if not materials:
        return "Draft", "warning"
    if all(m.publish_state == MaterialPublishState.PUBLISHED for m in materials):
        return "Published", "success"
    if any(m.publish_state == MaterialPublishState.PUBLISHED for m in materials):
        return "Published", "success"
    return "Draft", "warning"


async def get_lms_unit_chapter_management_page(
    scope: AccessScope,
    *,
    course_code: str | None = None,
) -> LmsUnitChapterManagementPageRead:
    authorize(scope, Permission.LMS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    courses = await CourseRecord.find(
        Eq(CourseRecord.tenant_id, tenant_id),
        Eq(CourseRecord.is_active, True),
    ).sort("+course_code").to_list()

    selected_code = (course_code or "").strip().upper()
    if not selected_code and courses:
        selected_code = (courses[0].course_code or "").upper()
    selected_course = next((c for c in courses if (c.course_code or "").upper() == selected_code), None)
    if selected_course is None and courses:
        selected_course = courses[0]
        selected_code = (selected_course.course_code or "").upper()

    course_options: list[LmsUnitChapterCourseOption] = []
    for course in courses:
        code = (course.course_code or "").upper()
        name = course.name or code
        course_options.append(
            LmsUnitChapterCourseOption(
                course_code=code,
                course_label=f"{code} · {name}",
                selected=code == selected_code,
            )
        )

    course_header = "—"
    unit_rows: list[LmsUnitChapterRow] = []
    empty_message = "No units defined for this course yet. Add units from the approved syllabus or upload materials with unit numbers."

    if selected_course and selected_code:
        course_header = f"{selected_code} · {selected_course.name or selected_code}"

        syllabus = await SyllabusRecord.find(
            Eq(SyllabusRecord.tenant_id, tenant_id),
            Eq(SyllabusRecord.course_id, selected_course.course_id),
        ).sort("-created_at").first_or_none()

        all_materials = await LearningMaterial.find(Eq(LearningMaterial.tenant_id, tenant_id)).to_list()
        materials = [d for d in all_materials if (d.course_code or "").upper() == selected_code]

        by_unit: dict[int, list[LearningMaterial]] = defaultdict(list)
        for doc in materials:
            if doc.unit_no is not None:
                by_unit[int(doc.unit_no)].append(doc)

        if syllabus and syllabus.units:
            for index, unit in enumerate(sorted(syllabus.units, key=lambda u: u.unit_no)):
                unit_no = unit.unit_no
                unit_materials = by_unit.get(unit_no, [])
                status_label, status_tone = _unit_status(unit_materials)

                counts_by_chapter: dict[str, int] = defaultdict(int)
                unassigned = 0
                for doc in unit_materials:
                    chapter = _chapter_key_from_material(doc)
                    if chapter:
                        counts_by_chapter[chapter] += 1
                    else:
                        unassigned += 1

                chapters: list[LmsChapterRow] = []
                topics = unit.topics or []
                if topics:
                    for topic_index, topic in enumerate(topics):
                        topic_label = topic.strip() if topic else f"Chapter {topic_index + 1}"
                        count = counts_by_chapter.get(topic_label, 0)
                        if topic_index == 0 and unassigned:
                            count += unassigned
                            unassigned = 0
                        chapters.append(
                            LmsChapterRow(
                                row_key=f"{selected_code}-u{unit_no}-c{topic_index}",
                                chapter_label=topic_label,
                                materials_count_label=_materials_count_label(count),
                                detail_href=f"/college-admin/lms/learning-material-management?course_code={selected_code}&unit_no={unit_no}",
                            )
                        )
                    for extra_label, extra_count in counts_by_chapter.items():
                        if extra_label not in {c.chapter_label for c in chapters}:
                            chapters.append(
                                LmsChapterRow(
                                    row_key=f"{selected_code}-u{unit_no}-x-{extra_label}",
                                    chapter_label=extra_label,
                                    materials_count_label=_materials_count_label(extra_count),
                                    detail_href=f"/college-admin/lms/learning-material-management?course_code={selected_code}&unit_no={unit_no}",
                                )
                            )
                elif unit_materials or unit.title:
                    chapters.append(
                        LmsChapterRow(
                            row_key=f"{selected_code}-u{unit_no}-c0",
                            chapter_label=unit.title or f"Unit {unit_no} content",
                            materials_count_label=_materials_count_label(len(unit_materials)),
                            detail_href=f"/college-admin/lms/learning-material-management?course_code={selected_code}&unit_no={unit_no}",
                        )
                    )

                unit_title = unit.title.strip() if unit.title else "Unit"
                unit_rows.append(
                    LmsUnitChapterRow(
                        row_key=f"{selected_code}-unit-{unit_no}",
                        unit_label=f"Unit {unit_no} – {unit_title}",
                        chapter_count_label=_chapter_count_label(len(chapters)),
                        status_label=status_label,
                        status_tone=status_tone,
                        default_expanded=index == 0,
                        chapters=chapters,
                    )
                )
        elif by_unit:
            for index, unit_no in enumerate(sorted(by_unit.keys())):
                unit_materials = by_unit[unit_no]
                status_label, status_tone = _unit_status(unit_materials)
                unit_rows.append(
                    LmsUnitChapterRow(
                        row_key=f"{selected_code}-unit-{unit_no}",
                        unit_label=f"Unit {unit_no}",
                        chapter_count_label=_chapter_count_label(1),
                        status_label=status_label,
                        status_tone=status_tone,
                        default_expanded=index == 0,
                        chapters=[
                            LmsChapterRow(
                                row_key=f"{selected_code}-u{unit_no}-c0",
                                chapter_label="All materials",
                                materials_count_label=_materials_count_label(len(unit_materials)),
                                detail_href=f"/college-admin/lms/learning-material-management?course_code={selected_code}&unit_no={unit_no}",
                            )
                        ],
                    )
                )
        elif not courses:
            empty_message = "No active courses found. Configure courses under LMS course management first."

    return LmsUnitChapterManagementPageRead(
        page_title="Unit & Chapter Management",
        page_subtitle="Course structure",
        export_label="Export",
        primary_action_label="Add unit",
        primary_action_href=(
            f"/college-admin/academics/curriculum-management"
            f"{f'?course_code={selected_code}' if selected_code else ''}"
        ),
        course_header_label=course_header,
        course_options=course_options,
        unit_rows=unit_rows,
        empty_message=empty_message,
        generated_at=now,
    )