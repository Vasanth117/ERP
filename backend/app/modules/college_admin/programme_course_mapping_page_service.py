"""Programme & course mapping page (CA 04.08 — organization)."""

from __future__ import annotations

from collections import defaultdict

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.modules.academics.curriculum_models import CourseRecord, EnrollmentRosterEntry
from app.modules.college_admin.academic_config_models import AcademicProgramme
from app.modules.college_admin.department_performance_overview_service import _programme_level
from app.modules.college_admin.identity_models import DepartmentKind, DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    CourseLoadBarItem,
    OrganizationModuleEmptyState,
    ProgrammeCourseMappingDepartmentTab,
    ProgrammeCourseMappingPageRead,
    ProgrammeOwnedRow,
    ServiceCourseRow,
    UnmappedCourseItem,
)
from app.modules.students.curriculum_models import CourseCatalogReference, CurriculumReference
from app.modules.students.models import StudentProfile
from app.modules.students.registration_enums import CourseRegistrationType

_TAB_LIMIT = 5
_LEVEL_LABEL = {
    "undergraduate": "UG",
    "postgraduate": "PG",
    "doctoral": "Doctoral",
}
_SERVICE_PREVIEW = 6
_UNMAPPED_PREVIEW = 4


def _duration_label(semesters: int) -> str:
    if semesters <= 4:
        return f"{max(1, semesters // 2)}-{semesters} years" if semesters > 2 else f"{semesters} semesters"
    years = semesters / 2
    if years == int(years):
        return f"{int(years)} years"
    return f"{years:.1f} years"


def _intake_label(prog: AcademicProgramme, dept: InstitutionDepartment) -> str:
    if _programme_level(prog) == "undergraduate" and dept.approved_intake_ug:
        return str(dept.approved_intake_ug)
    return "—"


def _regulation_label(
    programme_code: str,
    curriculum_by_prog: dict[str, list[CurriculumReference]],
) -> str:
    rows = curriculum_by_prog.get(programme_code.upper(), [])
    if not rows:
        return "—"
    for row in sorted(rows, key=lambda r: (r.academic_year_label, r.semester_label), reverse=True):
        if row.academic_regulations:
            return row.academic_regulations[0]
        if row.central_version:
            return row.central_version
    return "—"


def _mapped_status(prog: AcademicProgramme, dept: InstitutionDepartment) -> tuple[str, str, str]:
    code = prog.programme_code.upper()
    on_dept = prog.department_id == dept.id or code in {c.upper() for c in dept.programme_codes}
    if on_dept and prog.is_active:
        return "mapped", "Mapped", "success"
    if prog.is_active:
        return "linked", "Linked", "info"
    return "draft", "Draft", "warning"


def _empty_programme_course_mapping_page() -> ProgrammeCourseMappingPageRead:
    headers = ["Programme", "Level", "Duration", "Intake", "Regulation", "Status"]
    service_headers = ["Course", "Taught to", "Semester", "Students"]
    course_load = [
        CourseLoadBarItem(key="core", label="Core courses", value=0, max_value=1),
        CourseLoadBarItem(key="elective", label="Electives", value=0, max_value=1),
        CourseLoadBarItem(key="service", label="Service courses", value=0, max_value=1),
    ]
    return ProgrammeCourseMappingPageRead(
        page_title="Programme & Course Mapping",
        page_subtitle="Which programmes and courses each department offers and teaches",
        export_label="Export",
        map_programme_label="Map programme",
        map_programme_href="/college-admin/academics/academic-configuration-dashboard",
        department_tabs=[],
        more_departments=[],
        selected_department_id="",
        selected_department_name="—",
        programmes_section_title="Programmes owned by department",
        programmes_table_headers=headers,
        programmes=[],
        programmes_count_label="0 programmes",
        academic_configuration_label="Academic configuration →",
        academic_configuration_href="/college-admin/academics/academic-configuration-dashboard",
        service_courses_section_title="Service courses taught to other departments",
        service_table_headers=service_headers,
        service_courses=[],
        service_courses_count_label="0 service courses",
        service_view_all_label="View all →",
        service_view_all_href="/college-admin/organization/programme-course-mapping",
        unmapped_section_title="Unmapped items",
        unmapped_items=[],
        course_load_section_title="Course load",
        course_load_bars=course_load,
        footer_disclaimer="Live institutional data · Programmes, courses and catalog · All times IST",
        footer_snapshot_label="Live snapshot",
        setup_empty_state=OrganizationModuleEmptyState(
            title="No departments yet",
            description="Create academic departments first, then map programmes and service courses to them.",
            highlights=[
                "Programmes owned by each department",
                "Service courses taught across programmes",
                "Unmapped catalog items and course load",
            ],
            primary_label="Create department",
            primary_href="/college-admin/organization/create-department",
            secondary_label="View all departments",
            secondary_href="/college-admin/organization/all-departments",
        ),
        generated_at=utcnow(),
    )


def _taught_to_label(programme_codes: set[str], prog_by_code: dict[str, AcademicProgramme]) -> str:
    if not programme_codes:
        return "—"
    if len(programme_codes) >= 4:
        ug_only = all(_programme_level(prog_by_code[c]) == "undergraduate" for c in programme_codes if c in prog_by_code)
        if ug_only and len(programme_codes) >= 6:
            return "All UG programmes"
    labels: list[str] = []
    for code in sorted(programme_codes):
        prog = prog_by_code.get(code)
        if prog:
            labels.append(prog.name.split()[-1] if len(prog.name) > 20 else prog.programme_code)
        else:
            labels.append(code)
    return ", ".join(labels[:5]) + ("…" if len(labels) > 5 else "")


async def get_programme_course_mapping_page(
    scope: AccessScope,
    *,
    department_id: str | None = None,
) -> ProgrammeCourseMappingPageRead:
    authorize(scope, Permission.INSTITUTION_ORG_READ)
    tenant_id = require_college_tenant_scope(scope)

    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        In(InstitutionDepartment.status, [DepartmentStatus.ACTIVE, DepartmentStatus.DRAFT]),
    ).sort("+department_code").to_list()
    academic_departments = [
        d
        for d in departments
        if d.department_kind == DepartmentKind.ACADEMIC or d.programme_codes or d.organization_unit_id
    ]
    if not academic_departments:
        academic_departments = list(departments)

    selected_oid: PydanticObjectId | None = None
    if department_id:
        selected_oid = to_object_id(department_id, "department_id")
    if selected_oid is None or not any(d.id == selected_oid for d in academic_departments):
        selected_oid = academic_departments[0].id if academic_departments else None
    if selected_oid is None:
        return _empty_programme_course_mapping_page()

    dept = next(d for d in academic_departments if d.id == selected_oid)

    tabs_all = [
        ProgrammeCourseMappingDepartmentTab(
            department_id=str(d.id),
            tab_label=d.department_code,
            is_selected=d.id == selected_oid,
        )
        for d in academic_departments
    ]
    visible_tabs = tabs_all[:_TAB_LIMIT]
    more_tabs = tabs_all[_TAB_LIMIT:] if len(tabs_all) > _TAB_LIMIT else []

    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    prog_by_code = {p.programme_code.upper(): p for p in programmes}
    prog_codes_on_dept = {c.upper() for c in dept.programme_codes}

    dept_programmes = [
        p
        for p in programmes
        if p.is_active
        and (p.department_id == dept.id or p.programme_code.upper() in prog_codes_on_dept)
    ]

    curriculum_rows = await CurriculumReference.find(Eq(CurriculumReference.tenant_id, tenant_id)).to_list()
    curriculum_by_prog: dict[str, list[CurriculumReference]] = defaultdict(list)
    for row in curriculum_rows:
        curriculum_by_prog[row.programme_code.upper()].append(row)

    owned_rows: list[ProgrammeOwnedRow] = []
    for prog in sorted(dept_programmes, key=lambda row: row.name):
        level = _programme_level(prog)
        status_code, status_label, status_tone = _mapped_status(prog, dept)
        owned_rows.append(
            ProgrammeOwnedRow(
                programme_id=str(prog.id),
                programme_name=prog.name,
                level_label=_LEVEL_LABEL.get(level, "UG"),
                duration_label=_duration_label(prog.duration_semesters),
                intake_label=_intake_label(prog, dept),
                regulation_label=_regulation_label(prog.programme_code, curriculum_by_prog),
                status_code=status_code,
                status_label=status_label,
                status_tone=status_tone,
            )
        )

    courses = await CourseRecord.find(Eq(CourseRecord.tenant_id, tenant_id), Eq(CourseRecord.is_active, True)).to_list()
    owned_courses = [c for c in courses if c.department_id == dept.id]
    course_by_code = {c.course_code.upper(): c for c in courses}

    catalog = await CourseCatalogReference.find(Eq(CourseCatalogReference.tenant_id, tenant_id)).to_list()
    catalog_by_course: dict[str, list[CourseCatalogReference]] = defaultdict(list)
    for row in catalog:
        catalog_by_course[row.course_code.upper()].append(row)

    roster = await EnrollmentRosterEntry.find(Eq(EnrollmentRosterEntry.tenant_id, tenant_id)).to_list()
    roster_by_course: dict[str, set[PydanticObjectId]] = defaultdict(set)
    for entry in roster:
        roster_by_course[entry.course_code.upper()].add(entry.student_user_id)

    dept_prog_codes = {p.programme_code.upper() for p in dept_programmes}
    all_ug_codes = {
        p.programme_code.upper()
        for p in programmes
        if p.is_active and _programme_level(p) == "undergraduate"
    }

    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    students_by_programme: dict[str, int] = defaultdict(int)
    for profile in profiles:
        code = (profile.programme_code or "").upper()
        if code:
            students_by_programme[code] += 1

    service_rows: list[ServiceCourseRow] = []
    for course in owned_courses:
        refs = catalog_by_course.get(course.course_code.upper(), [])
        external_prog_codes: set[str] = set()
        semester_labels: set[str] = set()
        for ref in refs:
            code = ref.programme_code.upper()
            semester_labels.add(ref.semester_label)
            if code not in dept_prog_codes:
                external_prog_codes.add(code)
        if not external_prog_codes and refs:
            continue
        if not external_prog_codes:
            continue
        taught_to = _taught_to_label(external_prog_codes, prog_by_code)
        if external_prog_codes == all_ug_codes and len(external_prog_codes) > 3:
            taught_to = "All UG programmes"
        student_count = len(roster_by_course.get(course.course_code.upper(), set()))
        if not student_count:
            student_count = sum(students_by_programme.get(code, 0) for code in external_prog_codes)
        semester_label = sorted(semester_labels, key=lambda s: int(s) if s.isdigit() else s)[0] if semester_labels else "—"
        service_rows.append(
            ServiceCourseRow(
                course_id=course.course_id,
                course_label=f"{course.course_code} {course.name}",
                taught_to_label=taught_to,
                semester_label=semester_label,
                student_count=student_count,
            )
        )
    service_rows.sort(key=lambda row: row.course_label)
    service_preview = service_rows[:_SERVICE_PREVIEW]

    dept_by_id = {d.id: d for d in departments}
    seen_unmapped: set[str] = set()
    unmapped: list[UnmappedCourseItem] = []
    for course in courses:
        code_key = course.course_code.upper()
        if code_key in seen_unmapped:
            continue
        refs = catalog_by_course.get(code_key, [])
        if course.department_id is None:
            detail = (
                "Open elective – no owning department"
                if any(r.registration_type == CourseRegistrationType.OPEN for r in refs)
                else "No owning department in academic config"
            )
            unmapped.append(
                UnmappedCourseItem(
                    course_id=course.course_id,
                    course_label=f"{course.course_code} {course.name}",
                    detail=detail,
                    action_code="assign",
                    action_label="Assign",
                    action_tone="warning",
                )
            )
            seen_unmapped.add(code_key)
            continue
        if course.department_id != dept.id:
            owner = dept_by_id.get(course.department_id)
            if owner and any(r.programme_code.upper() in prog_codes_on_dept for r in refs):
                unmapped.append(
                    UnmappedCourseItem(
                        course_id=course.course_id,
                        course_label=f"{course.course_code} {course.name}",
                        detail=f"Shared with {owner.name}",
                        action_code="review",
                        action_label="Review",
                        action_tone="info",
                    )
                )
                seen_unmapped.add(code_key)
            continue
        if course.department_id == dept.id and refs and not any(
            r.programme_code.upper() in dept_prog_codes for r in refs
        ):
            unmapped.append(
                UnmappedCourseItem(
                    course_id=course.course_id,
                    course_label=f"{course.course_code} {course.name}",
                    detail="Not mapped to department programmes",
                    action_code="review",
                    action_label="Review",
                    action_tone="info",
                )
            )
            seen_unmapped.add(code_key)
        if len(unmapped) >= _UNMAPPED_PREVIEW:
            break
    unmapped = unmapped[:_UNMAPPED_PREVIEW]

    core_count = elective_count = service_count = 0
    for course in owned_courses:
        refs = catalog_by_course.get(course.course_code.upper(), [])
        types = {r.registration_type for r in refs}
        external = any(r.programme_code.upper() not in dept_prog_codes for r in refs)
        if external:
            service_count += 1
        elif CourseRegistrationType.OPEN in types:
            elective_count += 1
        elif CourseRegistrationType.ELECTIVE in types and CourseRegistrationType.CORE not in types:
            elective_count += 1
        else:
            core_count += 1
    if not owned_courses:
        core_count = elective_count = service_count = 0
    elif core_count == elective_count == service_count == 0:
        core_count = len(owned_courses) - len(service_rows)
        service_count = len(service_rows)
        elective_count = max(0, len(owned_courses) - core_count - service_count)

    max_load = max(core_count, elective_count, service_count, 1)
    course_load = [
        CourseLoadBarItem(key="core", label="Core courses", value=core_count, max_value=max_load),
        CourseLoadBarItem(key="elective", label="Electives", value=elective_count, max_value=max_load),
        CourseLoadBarItem(key="service", label="Service courses", value=service_count, max_value=max_load),
    ]

    return ProgrammeCourseMappingPageRead(
        page_title="Programme & Course Mapping",
        page_subtitle="Which programmes and courses each department offers and teaches",
        export_label="Export",
        map_programme_label="Map programme",
        map_programme_href="/college-admin/academics/academic-configuration-dashboard",
        department_tabs=visible_tabs,
        more_departments=more_tabs,
        selected_department_id=str(dept.id),
        selected_department_name=dept.name,
        programmes_section_title=f"Programmes owned by {dept.department_code}",
        programmes_table_headers=["Programme", "Level", "Duration", "Intake", "Regulation", "Status"],
        programmes=owned_rows,
        programmes_count_label=f"{len(owned_rows)} programme{'s' if len(owned_rows) != 1 else ''}",
        academic_configuration_label="Academic configuration →",
        academic_configuration_href="/college-admin/academics/academic-configuration-dashboard",
        service_courses_section_title="Service courses taught to other departments",
        service_table_headers=["Course", "Taught to", "Semester", "Students"],
        service_courses=service_preview,
        service_courses_count_label=f"{len(service_rows)} service course{'s' if len(service_rows) != 1 else ''}",
        service_view_all_label="View all →",
        service_view_all_href=f"/college-admin/organization/programme-course-mapping?departmentId={dept.id}&view=service",
        unmapped_section_title="Unmapped items",
        unmapped_items=unmapped,
        course_load_section_title="Course load",
        course_load_bars=course_load,
        footer_disclaimer="Live institutional data · Programmes, courses and catalog · All times IST",
        footer_snapshot_label="Live snapshot",
        generated_at=utcnow(),
    )