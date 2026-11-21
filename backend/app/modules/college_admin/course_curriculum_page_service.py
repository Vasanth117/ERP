"""Course configuration, curriculum & subject management pages (CA 05)."""

from __future__ import annotations

import math
import re
from collections import defaultdict
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.academics.curriculum_models import CourseLearningOutcome, CourseRecord, CurriculumRecord
from app.modules.audit.service import record_audit
from app.modules.college_admin.academic_config_models import AcademicProgramme
from app.modules.college_admin.course_curriculum_nav import (
    course_configuration_href,
    course_curriculum_sub_nav,
    new_course_configuration_href,
)
from app.modules.college_admin.identity_models import DepartmentKind, DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AcademicYearCreateFormField,
    AcademicYearCreateFormOption,
    CourseConfigurationForm,
    CourseConfigurationOfferedRow,
    CourseConfigurationPageRead,
    CourseConfigurationPrerequisiteRow,
    CourseConfigurationSave,
    CurriculumCreditCategoryRow,
    CurriculumManagementCourseRow,
    CurriculumManagementPageRead,
    CurriculumSemesterTab,
    CurriculumSummaryField,
    InstitutionPolicyFilterOption,
    PoliciesPagination,
    SubjectManagementPageRead,
    SubjectManagementTableRow,
)
from app.modules.students.curriculum_models import CourseCatalogReference, CoursePrerequisite, CurriculumReference
from app.modules.students.registration_enums import CourseRegistrationType

_SUBJECT_PAGE_SIZE = 8

_TYPE_LABELS = {
    CourseRegistrationType.CORE.value: "Professional core",
    CourseRegistrationType.ELECTIVE.value: "Professional elective",
    CourseRegistrationType.OPEN.value: "Open elective",
}

_DEFAULT_COURSE_TYPES = [
    ("professional_core", "Professional core"),
    ("basic_science", "Basic science"),
    ("mandatory", "Mandatory"),
    ("humanities", "Humanities"),
    ("elective", "Professional elective"),
    ("open_elective", "Open elective"),
]

_EXAM_DURATIONS = ["1 hour", "2 hours", "3 hours"]
_EXAM_TYPES = ["Theory", "Lab", "Theory + lab", "Project"]


def _parse_semester_number(label: str) -> int | None:
    if not label:
        return None
    match = re.search(r"(\d+)", label)
    return int(match.group(1)) if match else None


def _semester_tab_label(n: int) -> str:
    return f"Sem {n}"


def _ltp_label(course: CourseRecord) -> str:
    return f"{course.lecture_hours}-{course.tutorial_hours}-{course.practical_hours}"


def _derived_credits(course: CourseRecord) -> float:
    if course.credit_units > 0:
        return float(course.credit_units)
    return float(course.lecture_hours) + course.tutorial_hours / 2 + course.practical_hours / 2


def _course_type_label(raw: str | None) -> str:
    if not raw:
        return "—"
    for key, label in _DEFAULT_COURSE_TYPES:
        if key == raw or label.lower() == raw.lower():
            return label
    return raw.replace("_", " ").title()


def _subject_status(course: CourseRecord) -> tuple[str, str, str]:
    if not course.is_active:
        reg = (course.regulation_label or "").upper()
        if reg and reg not in {"R2023", "R2021"}:
            return "legacy", f"{reg} only", "muted"
        return "legacy", "Inactive", "muted"
    if course.department_id is None:
        return "no_owner", "No owner", "warning"
    if course.configuration_status == "active":
        return "active", "Active", "success"
    if course.configuration_status == "draft":
        return "draft", "Draft", "warning"
    return "active", "Active", "success"


def _curriculum_course_status(course: CourseRecord, curriculum_row: CurriculumRecord | None) -> tuple[str, str, str]:
    if curriculum_row and curriculum_row.approved:
        return "approved", "Approved", "success"
    if course.configuration_status == "draft":
        return "pending", "Options pending", "warning"
    return "approved", "Approved", "success"


async def get_subject_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    search: str | None = None,
    department_id: str | None = None,
    type_filter: str | None = None,
    regulation_filter: str | None = None,
    semester_filter: str | None = None,
) -> SubjectManagementPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_READ)
    tenant_id = require_college_tenant_scope(scope)
    dept_oid = to_object_id(department_id, "department_id") if department_id else None
    needle = (search or "").strip().lower()
    sem_filter = (semester_filter or "").strip()

    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.department_kind, DepartmentKind.ACADEMIC),
    ).to_list()
    dept_by_id = {str(d.id): d for d in departments if d.status != DepartmentStatus.ARCHIVED}

    courses = await CourseRecord.find(Eq(CourseRecord.tenant_id, tenant_id)).sort("+course_code").to_list()

    regulation_labels: set[str] = set()
    type_labels: set[str] = set()
    for course in courses:
        if course.regulation_label:
            regulation_labels.add(course.regulation_label)
        if course.course_type:
            type_labels.add(course.course_type)

    filtered: list[CourseRecord] = []
    for course in courses:
        if needle and needle not in f"{course.name} {course.course_code}".lower():
            continue
        if dept_oid and course.department_id != dept_oid:
            continue
        if type_filter and (course.course_type or "") != type_filter:
            continue
        if regulation_filter and (course.regulation_label or "") != regulation_filter:
            continue
        if sem_filter and str(course.semester_number or "") != sem_filter:
            continue
        filtered.append(course)

    total = len(filtered)
    total_pages = max(1, math.ceil(total / _SUBJECT_PAGE_SIZE)) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _SUBJECT_PAGE_SIZE
    page_slice = filtered[start : start + _SUBJECT_PAGE_SIZE]

    rows: list[SubjectManagementTableRow] = []
    for course in page_slice:
        dept = dept_by_id.get(str(course.department_id)) if course.department_id else None
        status_code, status_label, status_tone = _subject_status(course)
        rows.append(
            SubjectManagementTableRow(
                course_id=course.course_id,
                subject_name=course.name,
                subject_code=course.course_code,
                department_label=dept.department_code if dept else "—",
                type_label=_course_type_label(course.course_type),
                credits_label=str(int(_derived_credits(course))) if _derived_credits(course) == int(_derived_credits(course)) else f"{_derived_credits(course):.1f}",
                semester_label=str(course.semester_number) if course.semester_number else "—",
                status_code=status_code,
                status_label=status_label,
                status_tone=status_tone,
                configuration_href=course_configuration_href(course.course_id),
            )
        )

    page_numbers = list(range(1, min(total_pages, 12) + 1)) if total_pages else []
    if total_pages > 12:
        page_numbers = [1, 2, 3, -1, total_pages]

    all_count = len(courses)
    count_label = f"{all_count:,} subject{'s' if all_count != 1 else ''}" if all_count else "No subjects"

    dept_options = [InstitutionPolicyFilterOption(value="", label="All departments")]
    for dept in sorted(dept_by_id.values(), key=lambda d: d.department_code):
        dept_options.append(InstitutionPolicyFilterOption(value=str(dept.id), label=dept.department_code))

    type_options = [InstitutionPolicyFilterOption(value="", label="All types")]
    for key, label in _DEFAULT_COURSE_TYPES:
        if key in type_labels or not type_labels:
            type_options.append(InstitutionPolicyFilterOption(value=key, label=label))

    reg_options = [InstitutionPolicyFilterOption(value="", label="All regulations")]
    for label in sorted(regulation_labels):
        reg_options.append(InstitutionPolicyFilterOption(value=label, label=label))

    sem_options = [InstitutionPolicyFilterOption(value="", label="All semesters")]
    for n in range(1, 9):
        sem_options.append(InstitutionPolicyFilterOption(value=str(n), label=str(n)))

    shown = len(rows)
    showing_label = f"Showing {shown} of {total:,}" if total else "Showing 0 of 0"

    return SubjectManagementPageRead(
        page_title="Subject Management",
        page_subtitle="Master list of subjects across all departments and regulations",
        import_label="Import subjects",
        add_subject_label="Add subject",
        add_subject_href=new_course_configuration_href(),
        search_placeholder="Search subject code or title...",
        department_filter_label="Department",
        type_filter_label="Type",
        regulation_filter_label="Regulation",
        semester_filter_label="Semester",
        department_options=dept_options,
        type_options=type_options,
        regulation_options=reg_options,
        semester_options=sem_options,
        subjects_section_title="Subjects",
        subjects_count_label=count_label,
        table_headers=["Subject", "Code", "Department", "Type", "Credits", "Semester", "Status"],
        subjects=rows,
        showing_label=showing_label,
        pagination=PoliciesPagination(
            page=page,
            page_size=_SUBJECT_PAGE_SIZE,
            total=total,
            total_pages=total_pages,
            page_numbers=page_numbers,
            has_previous=page > 1 and bool(total),
            has_next=page < total_pages,
        ),
        sub_nav=course_curriculum_sub_nav(active="subjects"),
        footer_disclaimer="Live academic data · Course and subject registry · All times IST",
        footer_snapshot_label="Live snapshot",
        generated_at=utcnow(),
    )


async def get_curriculum_management_page(
    scope: AccessScope,
    *,
    programme_id: str | None = None,
    semester: int = 4,
) -> CurriculumManagementPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_READ)
    tenant_id = require_college_tenant_scope(scope)

    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id), Eq(AcademicProgramme.is_active, True)).sort("+name").to_list()
    if not programmes:
        return CurriculumManagementPageRead(
            page_title="Curriculum Management",
            page_subtitle="No programmes configured yet",
            download_pdf_label="Download PDF",
            subjects_button_label="Subjects",
            subjects_button_href="/college-admin/academics/subject-management",
            edit_curriculum_label="Edit curriculum",
            edit_curriculum_href=new_course_configuration_href(),
            programme_options=[],
            selected_programme_id=None,
            selected_programme_label="—",
            regulation_label="—",
            semester_tabs=[],
            selected_semester=semester,
            courses_panel_title=f"Semester {semester} courses",
            courses_panel_meta="0 credits • 0 courses",
            table_headers=["Course", "Type", "L-T-P", "Credits", "Status"],
            courses=[],
            approval_footer_label="—",
            version_history_label="Version history →",
            version_history_href="/college-admin/academics/academic-configuration-history",
            credits_panel_title="Programme credits",
            credit_categories=[],
            summary_panel_title="Curriculum summary",
            summary_fields=[],
            sub_nav=course_curriculum_sub_nav(active="curriculum"),
            footer_disclaimer="Live academic data · Curriculum references · All times IST",
            footer_snapshot_label="Live snapshot",
            generated_at=utcnow(),
        )

    prog_oid = to_object_id(programme_id, "programme_id") if programme_id else programmes[0].id
    selected = next((p for p in programmes if p.id == prog_oid), programmes[0])
    prog_code = selected.programme_code.upper()
    duration_semesters = max(4, min(selected.duration_semesters, 12))
    semester = max(1, min(semester, duration_semesters))

    curriculum_refs = await CurriculumReference.find(Eq(CurriculumReference.tenant_id, tenant_id)).to_list()
    prog_refs = [r for r in curriculum_refs if r.programme_code.upper() == prog_code]
    regulation_label = "—"
    if prog_refs:
        for ref in sorted(prog_refs, key=lambda r: r.updated_at, reverse=True):
            if ref.academic_regulations:
                regulation_label = ref.academic_regulations[0]
                break
            if ref.central_version:
                regulation_label = ref.central_version
                break

    catalog = await CourseCatalogReference.find(Eq(CourseCatalogReference.tenant_id, tenant_id)).to_list()
    prog_catalog = [c for c in catalog if c.programme_code.upper() == prog_code]

    courses_all = await CourseRecord.find(Eq(CourseRecord.tenant_id, tenant_id)).to_list()
    course_by_id = {c.course_id: c for c in courses_all}
    course_by_code = {c.course_code.upper(): c for c in courses_all}

    curriculum_records = await CurriculumRecord.find(Eq(CurriculumRecord.tenant_id, tenant_id)).to_list()
    curriculum_by_course: dict[str, CurriculumRecord] = {}
    for row in curriculum_records:
        curriculum_by_course[row.course_id] = row

    semester_tabs = [
        CurriculumSemesterTab(semester_number=n, tab_label=_semester_tab_label(n), is_selected=n == semester)
        for n in range(1, duration_semesters + 1)
    ]

    semester_key = str(semester)
    sem_catalog = [
        c
        for c in prog_catalog
        if _parse_semester_number(c.semester_label) == semester or c.semester_label.strip() == semester_key
    ]

    if not sem_catalog:
        sem_catalog = [
            c
            for c in prog_catalog
            if course_by_code.get(c.course_code.upper())
            and (course_by_code[c.course_code.upper()].semester_number == semester)
        ]

    table_rows: list[CurriculumManagementCourseRow] = []
    total_credits = 0.0
    for entry in sorted(sem_catalog, key=lambda e: e.course_code):
        course = course_by_id.get(entry.course_id) or course_by_code.get(entry.course_code.upper())
        if not course:
            continue
        credits = entry.credit_units or _derived_credits(course)
        total_credits += credits
        type_label = _TYPE_LABELS.get(entry.registration_type.value, _course_type_label(course.course_type))
        cur_row = curriculum_by_course.get(course.course_id)
        status_code, status_label, status_tone = _curriculum_course_status(course, cur_row)
        table_rows.append(
            CurriculumManagementCourseRow(
                course_id=course.course_id,
                course_code=course.course_code,
                course_name=course.name,
                type_label=type_label,
                ltp_label=_ltp_label(course),
                credits_label=str(int(credits)) if credits == int(credits) else f"{credits:.1f}",
                status_code=status_code,
                status_label=status_label,
                status_tone=status_tone,
                configuration_href=course_configuration_href(course.course_id),
            )
        )

    if not table_rows:
        for course in sorted(
            [c for c in courses_all if c.semester_number == semester],
            key=lambda c: c.course_code,
        ):
            credits = _derived_credits(course)
            total_credits += credits
            cur_row = curriculum_by_course.get(course.course_id)
            status_code, status_label, status_tone = _curriculum_course_status(course, cur_row)
            table_rows.append(
                CurriculumManagementCourseRow(
                    course_id=course.course_id,
                    course_code=course.course_code,
                    course_name=course.name,
                    type_label=_course_type_label(course.course_type),
                    ltp_label=_ltp_label(course),
                    credits_label=str(int(credits)) if credits == int(credits) else f"{credits:.1f}",
                    status_code=status_code,
                    status_label=status_label,
                    status_tone=status_tone,
                    configuration_href=course_configuration_href(course.course_id),
                )
            )

    credits_by_category: dict[str, float] = defaultdict(float)
    for entry in prog_catalog:
        course = course_by_id.get(entry.course_id) or course_by_code.get(entry.course_code.upper())
        cr = entry.credit_units or (_derived_credits(course) if course else 0)
        key = entry.registration_type.value
        credits_by_category[key] += cr

    if not credits_by_category:
        for course in courses_all:
            key = (course.course_type or "core").split("_")[0] if course.course_type else "core"
            credits_by_category[key] += _derived_credits(course)

    total_prog_credits = sum(credits_by_category.values()) or sum(_derived_credits(c) for c in courses_all)
    credit_rows: list[CurriculumCreditCategoryRow] = []
    for key, credits in sorted(credits_by_category.items(), key=lambda item: -item[1]):
        label = _TYPE_LABELS.get(key, key.replace("_", " ").title())
        share = round((credits / total_prog_credits) * 100, 1) if total_prog_credits else None
        credit_rows.append(
            CurriculumCreditCategoryRow(
                category_key=key,
                category_label=label,
                credits=credits,
                share_pct=share,
            )
        )

    latest_curriculum = sorted(prog_refs, key=lambda r: r.updated_at, reverse=True)[0] if prog_refs else None
    approved_label = "—"
    if latest_curriculum:
        recs = [r for r in curriculum_records if r.approved]
        if recs:
            latest_rec = max(recs, key=lambda r: r.approved_at or r.created_at)
            approved_label = f"Approved · {latest_rec.approved_at.strftime('%d %b %Y') if latest_rec.approved_at else 'Board of Studies'}"

    summary_fields = [
        CurriculumSummaryField(key="total_credits", label="Total credits", value=str(int(total_prog_credits))),
        CurriculumSummaryField(key="approved_by", label="Approved by", value="Board of Studies"),
        CurriculumSummaryField(
            key="version",
            label="Version",
            value=latest_curriculum.central_version if latest_curriculum and latest_curriculum.central_version else regulation_label,
        ),
        CurriculumSummaryField(key="batches", label="Applies to batches", value="From current regulation"),
    ]

    programme_options = [
        AcademicYearCreateFormOption(value=str(p.id), label=p.name) for p in programmes
    ]

    subtitle = f"Semester-wise curriculum for {selected.name}"
    if regulation_label != "—":
        subtitle = f"{subtitle} ({regulation_label})"

    return CurriculumManagementPageRead(
        page_title="Curriculum Management",
        page_subtitle=subtitle,
        download_pdf_label="Download PDF",
        subjects_button_label="Subjects",
        subjects_button_href="/college-admin/academics/subject-management",
        edit_curriculum_label="Edit curriculum",
        edit_curriculum_href=new_course_configuration_href(),
        programme_options=programme_options,
        selected_programme_id=str(selected.id),
        selected_programme_label=selected.name,
        regulation_label=regulation_label,
        semester_tabs=semester_tabs,
        selected_semester=semester,
        courses_panel_title=f"Semester {semester} courses",
        courses_panel_meta=f"{int(total_credits)} credits • {len(table_rows)} courses",
        table_headers=["Course", "Type", "L-T-P", "Credits", "Status"],
        courses=table_rows,
        approval_footer_label=approved_label,
        version_history_label="Version history →",
        version_history_href="/college-admin/academics/academic-configuration-history",
        credits_panel_title=f"Programme credits ({regulation_label})",
        credit_categories=credit_rows,
        summary_panel_title="Curriculum summary",
        summary_fields=summary_fields,
        sub_nav=course_curriculum_sub_nav(active="curriculum"),
        footer_disclaimer="Live academic data · Curriculum and catalogue references · All times IST",
        footer_snapshot_label="Live snapshot",
        generated_at=utcnow(),
    )


async def _build_configuration_page(
    scope: AccessScope,
    *,
    course: CourseRecord | None,
    is_new: bool,
) -> CourseConfigurationPageRead:
    tenant_id = require_college_tenant_scope(scope)

    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.department_kind, DepartmentKind.ACADEMIC),
    ).to_list()
    dept_options = [AcademicYearCreateFormOption(value="", label="— Select department —")]
    for dept in sorted(departments, key=lambda d: d.name):
        if dept.status != DepartmentStatus.ARCHIVED:
            dept_options.append(
                AcademicYearCreateFormOption(value=str(dept.id), label=f"{dept.department_code} · {dept.name}")
            )

    regulation_labels: set[str] = set()
    existing = await CourseRecord.find(Eq(CourseRecord.tenant_id, tenant_id)).to_list()
    for row in existing:
        if row.regulation_label:
            regulation_labels.add(row.regulation_label)
    regulation_options = [AcademicYearCreateFormOption(value="", label="—")]
    for label in sorted(regulation_labels) or ["R2023"]:
        regulation_options.append(AcademicYearCreateFormOption(value=label, label=label))

    type_options = [AcademicYearCreateFormOption(value=k, label=l) for k, l in _DEFAULT_COURSE_TYPES]
    semester_options = [AcademicYearCreateFormOption(value=str(n), label=str(n)) for n in range(1, 9)]
    exam_duration_options = [AcademicYearCreateFormOption(value=v, label=v) for v in _EXAM_DURATIONS]
    exam_type_options = [AcademicYearCreateFormOption(value=v, label=v) for v in _EXAM_TYPES]

    if is_new or course is None:
        default_reg = regulation_options[1].value if len(regulation_options) > 1 else ""
        form = CourseConfigurationForm(
            course_id=None,
            course_code="",
            course_title="",
            department_id=None,
            course_type="",
            semester_number=None,
            regulation_label=default_reg,
            description="",
            lecture_hours=0,
            tutorial_hours=0,
            practical_hours=0,
            credit_units=0,
            internal_assessment_label="",
            end_semester_exam_label="",
            exam_duration_label="",
            exam_type_label="",
        )
        status_label, status_tone = "Draft", "warning"
        prerequisites: list[CourseConfigurationPrerequisiteRow] = []
        offered: list[CourseConfigurationOfferedRow] = []
        outcomes_text = None
    else:
        form = CourseConfigurationForm(
            course_id=course.course_id,
            course_code=course.course_code,
            course_title=course.name,
            department_id=str(course.department_id) if course.department_id else None,
            course_type=course.course_type,
            semester_number=course.semester_number,
            regulation_label=course.regulation_label,
            description=course.description,
            lecture_hours=course.lecture_hours,
            tutorial_hours=course.tutorial_hours,
            practical_hours=course.practical_hours,
            credit_units=_derived_credits(course),
            internal_assessment_label=course.internal_assessment_label,
            end_semester_exam_label=course.end_semester_exam_label,
            exam_duration_label=course.exam_duration_label,
            exam_type_label=course.exam_type_label,
        )
        status_label = "Active" if course.configuration_status == "active" else course.configuration_status.title()
        status_tone = "success" if course.configuration_status == "active" else "warning"

        prereq_doc = await CoursePrerequisite.find_one(
            Eq(CoursePrerequisite.tenant_id, tenant_id),
            Eq(CoursePrerequisite.course_id, course.course_id),
        )
        prerequisites = []
        if prereq_doc:
            for pid in prereq_doc.prerequisite_course_ids:
                pre = next((c for c in existing if c.course_id == pid), None)
                if pre:
                    prerequisites.append(
                        CourseConfigurationPrerequisiteRow(
                            prerequisite_id=pid,
                            title=f"{pre.course_code} {pre.name}",
                            semester_hint=f"Semester {pre.semester_number}" if pre.semester_number else None,
                            requirement_type="required",
                            requirement_label="Required",
                            requirement_tone="success",
                        )
                    )
            for pid in prereq_doc.corequisite_course_ids:
                pre = next((c for c in existing if c.course_id == pid), None)
                if pre:
                    prerequisites.append(
                        CourseConfigurationPrerequisiteRow(
                            prerequisite_id=pid,
                            title=f"{pre.course_code} {pre.name}",
                            semester_hint=f"Semester {pre.semester_number}" if pre.semester_number else None,
                            requirement_type="recommended",
                            requirement_label="Recommended",
                            requirement_tone="info",
                        )
                    )

        catalog = await CourseCatalogReference.find(Eq(CourseCatalogReference.tenant_id, tenant_id)).to_list()
        programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
        prog_by_code = {p.programme_code.upper(): p for p in programmes}
        offered = []
        for entry in catalog:
            if entry.course_id != course.course_id and entry.course_code.upper() != course.course_code.upper():
                continue
            prog = prog_by_code.get(entry.programme_code.upper())
            prog_label = prog.name if prog else entry.programme_code
            reg_type = _TYPE_LABELS.get(entry.registration_type.value, entry.registration_type.value)
            offered.append(
                CourseConfigurationOfferedRow(
                    programme_label=prog_label,
                    detail_label=f"{entry.semester_label} · {reg_type}",
                )
            )

        outcome_doc = await CourseLearningOutcome.find_one(
            Eq(CourseLearningOutcome.tenant_id, tenant_id),
            Eq(CourseLearningOutcome.course_id, course.course_id),
        )
        outcomes_text = "\n".join(outcome_doc.outcomes) if outcome_doc and outcome_doc.outcomes else None

    return CourseConfigurationPageRead(
        page_title="Course Configuration",
        page_subtitle="Configure a course: credits, hours, assessment and prerequisites",
        status_label=status_label,
        status_tone=status_tone,
        cancel_label="Cancel",
        save_label="Save course",
        form_note="Changes are saved to the audit log with your name and time.",
        details_section_title="Course details",
        hours_section_title="Hours & credits",
        assessment_section_title="Assessment",
        prerequisites_section_title="Prerequisites",
        offered_section_title="Offered to",
        outcomes_section_title="Outcomes",
        outcomes_edit_label="Edit →",
        outcomes_edit_href=course_configuration_href(form.course_id) if form.course_id else new_course_configuration_href(),
        field_meta=[
            AcademicYearCreateFormField(key="course_code", label="Course code", required=True),
            AcademicYearCreateFormField(key="course_title", label="Course title", required=True),
            AcademicYearCreateFormField(key="department_id", label="Offering department", required=True, field_type="select"),
            AcademicYearCreateFormField(key="course_type", label="Course type", required=True, field_type="select"),
            AcademicYearCreateFormField(key="semester_number", label="Semester", required=True, field_type="select"),
            AcademicYearCreateFormField(key="regulation_label", label="Regulation", required=True, field_type="select"),
            AcademicYearCreateFormField(key="description", label="Course description", field_type="textarea"),
            AcademicYearCreateFormField(key="lecture_hours", label="Lecture (L)", required=True, field_type="number"),
            AcademicYearCreateFormField(key="tutorial_hours", label="Tutorial (T)", required=True, field_type="number"),
            AcademicYearCreateFormField(key="practical_hours", label="Practical (P)", required=True, field_type="number"),
            AcademicYearCreateFormField(key="credit_units", label="Credits (C)", required=True, field_type="number"),
            AcademicYearCreateFormField(key="internal_assessment_label", label="Internal assessment", required=True),
            AcademicYearCreateFormField(key="end_semester_exam_label", label="End-semester exam", required=True),
            AcademicYearCreateFormField(key="exam_duration_label", label="Exam duration", required=True, field_type="select"),
            AcademicYearCreateFormField(key="exam_type_label", label="Exam type", required=True, field_type="select"),
        ],
        department_options=dept_options,
        course_type_options=type_options,
        semester_options=semester_options,
        regulation_options=regulation_options,
        exam_duration_options=exam_duration_options,
        exam_type_options=exam_type_options,
        form=form,
        prerequisites=prerequisites,
        offered_to=offered,
        outcomes_text=outcomes_text,
        sub_nav=course_curriculum_sub_nav(active="course_configuration"),
        footer_disclaimer="Live academic data · Official course registry · All times IST",
        footer_snapshot_label="Live snapshot",
        generated_at=utcnow(),
    )


async def get_course_configuration_page(
    scope: AccessScope,
    *,
    course_id: str | None = None,
    mode: str | None = None,
) -> CourseConfigurationPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_READ)
    tenant_id = require_college_tenant_scope(scope)
    is_new = mode == "create" or not course_id

    course: CourseRecord | None = None
    if course_id and not is_new:
        course = await CourseRecord.find_one(
            Eq(CourseRecord.tenant_id, tenant_id),
            Eq(CourseRecord.course_id, course_id),
        )
        if course is None:
            course = await CourseRecord.find_one(
                Eq(CourseRecord.tenant_id, tenant_id),
                Eq(CourseRecord.course_code, course_id.upper()),
            )
        if course is None:
            raise AppError("Course not found", status_code=404)
        is_new = False

    return await _build_configuration_page(scope, course=course, is_new=is_new)


async def save_course_configuration(
    scope: AccessScope,
    payload: CourseConfigurationSave,
) -> CourseConfigurationPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    form = payload.form
    code = form.course_code.strip().upper()
    if not code or not form.course_title.strip():
        raise AppError("Course code and title are required", status_code=400)

    dept_id = to_object_id(form.department_id, "department_id") if form.department_id else None
    credits = form.credit_units if form.credit_units > 0 else float(form.lecture_hours) + form.tutorial_hours / 2 + form.practical_hours / 2

    if form.course_id:
        course = await CourseRecord.find_one(
            Eq(CourseRecord.tenant_id, tenant_id),
            Eq(CourseRecord.course_id, form.course_id),
        )
        if course is None:
            raise AppError("Course not found", status_code=404)
        course.course_code = code
        course.name = form.course_title.strip()
        course.department_id = dept_id
        course.course_type = form.course_type
        course.semester_number = form.semester_number
        course.regulation_label = form.regulation_label
        course.description = form.description
        course.lecture_hours = form.lecture_hours
        course.tutorial_hours = form.tutorial_hours
        course.practical_hours = form.practical_hours
        course.credit_units = credits
        course.internal_assessment_label = form.internal_assessment_label
        course.end_semester_exam_label = form.end_semester_exam_label
        course.exam_duration_label = form.exam_duration_label
        course.exam_type_label = form.exam_type_label
        course.configuration_status = "active"
        course.updated_at = utcnow()
        await course.save()
        action = "academic.course.updated"
    else:
        if await CourseRecord.find_one(Eq(CourseRecord.tenant_id, tenant_id), Eq(CourseRecord.course_code, code)):
            raise AppError("Course code already exists", status_code=409)
        course_id = code.lower().replace(" ", "-") or str(uuid4())
        course = CourseRecord(
            tenant_id=tenant_id,
            course_id=course_id,
            course_code=code,
            name=form.course_title.strip(),
            department_id=dept_id,
            course_type=form.course_type,
            semester_number=form.semester_number,
            regulation_label=form.regulation_label,
            description=form.description,
            lecture_hours=form.lecture_hours,
            tutorial_hours=form.tutorial_hours,
            practical_hours=form.practical_hours,
            credit_units=credits,
            internal_assessment_label=form.internal_assessment_label,
            end_semester_exam_label=form.end_semester_exam_label,
            exam_duration_label=form.exam_duration_label,
            exam_type_label=form.exam_type_label,
            configuration_status="active",
        )
        await course.insert()
        action = "academic.course.created"

    await record_audit(
        actor_id=scope.user_id,
        action=action,
        resource_type="course",
        resource_id=course.course_id,
        tenant_id=tenant_id,
    )

    return await _build_configuration_page(scope, course=course, is_new=False)