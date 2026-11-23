"""Department management dashboard (CA 04 — organization / departments)."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import as_utc_aware, utcnow
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicProgramme, AcademicYear
from app.modules.college_admin.faculty_admin_models import FacultyEmploymentStatus, FacultyRecord
from app.modules.college_admin.identity_models import (
    DepartmentStaffAssociation,
    DepartmentStatus,
    InstitutionDepartment,
    InstitutionOrganizationUnit,
    OrganizationUnitType,
)
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    DepartmentAttentionTableRow,
    DepartmentEnrollmentBarItem,
    DepartmentManagementDashboardPageRead,
    DepartmentQuickActionItem,
    DepartmentSchoolBarItem,
    UserDashboardFilterOption,
    UserDashboardKpi,
)
from app.modules.college_admin.department_performance_overview_service import _programme_level
from app.modules.college_admin.institution_service import list_campuses
from app.modules.examinations.exam_cell_grading_enums import ExamSubjectResultOutcome
from app.modules.examinations.exam_cell_grading_models import ExamStudentSubjectResult
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.faculty.models import FacultyProfile
from app.modules.hr.enums import HrJobOpeningStatus
from app.modules.hr.recruitment_models import HrJobOpening
from app.modules.students.models import StudentProfile

_IST = ZoneInfo("Asia/Kolkata")
_reader = OperationalDataReader()

_ACTIVE_EMPLOYMENT = frozenset(
    {
        FacultyEmploymentStatus.ACTIVE,
        FacultyEmploymentStatus.CONFIRMED,
        FacultyEmploymentStatus.PROBATION,
        FacultyEmploymentStatus.AWAITING_CONFIRMATION,
        FacultyEmploymentStatus.ON_LEAVE,
    }
)

_MAX_CHART_BARS = 12
_MAX_ATTENTION_ROWS = 8


def _school_category_key(name: str) -> str:
    lower = name.lower()
    if "engineer" in lower:
        return "engineering"
    if "science" in lower:
        return "science"
    if "management" in lower or "business" in lower:
        return "management"
    return "other"


def _category_label(key: str) -> str:
    return {
        "engineering": "engineering",
        "science": "science",
        "management": "management",
    }.get(key, key)


async def get_department_management_dashboard_page(
    scope: AccessScope,
    *,
    academic_year_label: str | None = None,
    campus_id: str | None = None,
    school_id: str | None = None,
) -> DepartmentManagementDashboardPageRead:
    authorize(scope, Permission.INSTITUTION_ORG_READ)
    tenant_id = require_college_tenant_scope(scope)
    campus_oid = to_object_id(campus_id, "campus_id") if campus_id else None
    school_oid = to_object_id(school_id, "school_id") if school_id else None

    year_label, _sem = await _reader.current_academic_term(tenant_id)
    selected_year = academic_year_label or year_label

    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        In(InstitutionDepartment.status, [DepartmentStatus.ACTIVE, DepartmentStatus.DRAFT]),
    ).to_list()
    if campus_oid is not None:
        departments = [d for d in departments if campus_oid in d.campus_ids or not d.campus_ids]
    if school_oid is not None:
        departments = [d for d in departments if d.organization_unit_id == school_oid]

    org_units = await InstitutionOrganizationUnit.find(
        Eq(InstitutionOrganizationUnit.tenant_id, tenant_id),
        Eq(InstitutionOrganizationUnit.status, DepartmentStatus.ACTIVE),
    ).to_list()
    school_units = [u for u in org_units if u.unit_type == OrganizationUnitType.SCHOOL]
    unit_by_id = {u.id: u for u in org_units}

    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    active_programmes = [p for p in programmes if p.is_active]

    mapped_codes: set[str] = set()
    for dept in departments:
        for code in dept.programme_codes:
            mapped_codes.add(code.upper())
    for prog in active_programmes:
        if prog.department_id is not None:
            mapped_codes.add(prog.programme_code.upper())

    unmapped_programmes = [
        p
        for p in active_programmes
        if p.department_id is None and p.programme_code.upper() not in mapped_codes
    ]

    level_counts = {"undergraduate": 0, "postgraduate": 0, "doctoral": 0}
    for prog in active_programmes:
        level = _programme_level(prog)
        if level in level_counts:
            level_counts[level] += 1

    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    dept_ids = {d.id for d in departments}
    students_by_dept: dict[str, int] = defaultdict(int)
    total_students = 0
    for profile in profiles:
        if profile.department_id is None or profile.department_id not in dept_ids:
            continue
        students_by_dept[str(profile.department_id)] += 1
        total_students += 1

    faculty_by_dept: dict[str, int] = defaultdict(int)
    seen_faculty: set[PydanticObjectId] = set()
    faculty_records = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).to_list()
    for rec in faculty_records:
        if rec.employment_status not in _ACTIVE_EMPLOYMENT or rec.department_id is None:
            continue
        if rec.department_id not in dept_ids:
            continue
        faculty_by_dept[str(rec.department_id)] += 1
        seen_faculty.add(rec.user_id)
    faculty_profiles = await FacultyProfile.find(Eq(FacultyProfile.tenant_id, tenant_id)).to_list()
    for fp in faculty_profiles:
        if fp.user_id in seen_faculty or fp.department_id is None or fp.department_id not in dept_ids:
            continue
        faculty_by_dept[str(fp.department_id)] += 1

    total_faculty = sum(faculty_by_dept.values())
    dept_count = len(departments)
    avg_faculty = round(total_faculty / dept_count, 1) if dept_count else 0.0
    student_faculty_ratio = round(total_students / total_faculty) if total_faculty else None

    acting_heads: set[str] = set()
    associations = await DepartmentStaffAssociation.find(
        Eq(DepartmentStaffAssociation.tenant_id, tenant_id),
    ).to_list()
    for assoc in associations:
        if "acting" in (assoc.association_role or "").lower():
            acting_heads.add(str(assoc.department_id))

    head_user_ids = [d.head_user_id for d in departments if d.head_user_id]
    head_users = await User.find(In(User.id, head_user_ids)).to_list() if head_user_ids else []
    head_names = {u.id: u.full_name for u in head_users}

    filled_heads = sum(1 for d in departments if d.head_user_id)
    acting_count = sum(1 for d in departments if str(d.id) in acting_heads)
    vacant_heads = sum(1 for d in departments if not d.head_user_id)

    category_counts: dict[str, int] = defaultdict(int)
    school_bar_counts: dict[str, int] = defaultdict(int)
    for dept in departments:
        unit = unit_by_id.get(dept.organization_unit_id) if dept.organization_unit_id else None
        school_name = unit.name if unit else "Unassigned"
        school_bar_counts[school_name] += 1
        category_counts[_school_category_key(school_name if unit else dept.name)] += 1

    dept_hint_parts = [
        f"{category_counts[k]} {_category_label(k)}"
        for k in ("engineering", "science", "management")
        if category_counts.get(k, 0) > 0
    ]
    active_dept_count = sum(1 for d in departments if d.status == DepartmentStatus.ACTIVE)
    draft_dept_count = dept_count - active_dept_count
    if dept_hint_parts:
        departments_hint = " · ".join(dept_hint_parts)
    elif draft_dept_count:
        departments_hint = f"{active_dept_count} active · {draft_dept_count} draft"
    else:
        departments_hint = f"{active_dept_count} active"

    prog_hint_parts: list[str] = []
    if level_counts["undergraduate"]:
        prog_hint_parts.append(f"{level_counts['undergraduate']} UG")
    if level_counts["postgraduate"]:
        prog_hint_parts.append(f"{level_counts['postgraduate']} PG")
    if level_counts["doctoral"]:
        prog_hint_parts.append(f"{level_counts['doctoral']} Ph.D.")
    programmes_hint = " · ".join(prog_hint_parts) if prog_hint_parts else "No active programmes"

    kpis = [
        UserDashboardKpi(
            key="departments",
            label="Departments",
            value=f"{dept_count:,}" if dept_count else "0",
            hint_line=departments_hint,
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="programmes",
            label="Programmes offered",
            value=f"{len(active_programmes):,}" if active_programmes else "0",
            hint_line=programmes_hint,
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="hod_positions",
            label="HoD positions filled",
            value=f"{filled_heads} / {dept_count}" if dept_count else "0 / 0",
            hint_line=(
                f"{acting_count} acting HoD{'s' if acting_count != 1 else ''}"
                if acting_count
                else "All heads appointed"
            ),
            hint_tone="warning" if acting_count or vacant_heads else "success",
        ),
        UserDashboardKpi(
            key="avg_faculty",
            label="Avg. faculty per dept.",
            value=str(avg_faculty) if dept_count else "—",
            hint_line=(
                f"Ratio 1 : {student_faculty_ratio}"
                if student_faculty_ratio
                else "No faculty records yet"
            ),
            hint_tone="muted",
        ),
    ]

    enrollment_bars = sorted(
        [
            DepartmentEnrollmentBarItem(
                department_id=str(dept.id),
                department_code=dept.department_code,
                student_count=students_by_dept.get(str(dept.id), 0),
                faculty_count=faculty_by_dept.get(str(dept.id), 0),
            )
            for dept in departments
        ],
        key=lambda row: row.student_count,
        reverse=True,
    )[:_MAX_CHART_BARS]

    openings = await HrJobOpening.find(
        Eq(HrJobOpening.tenant_id, tenant_id),
        Eq(HrJobOpening.status, HrJobOpeningStatus.PUBLISHED),
    ).to_list()
    vacancies_by_dept: dict[str, int] = defaultdict(int)
    for opening in openings:
        open_slots = max(0, opening.vacancies - opening.filled_count)
        if open_slots <= 0:
            continue
        vacancies_by_dept[str(opening.department_id)] += open_slots
    vacancy_total = sum(vacancies_by_dept.values())

    exam_sessions = await ExamSession.find(Eq(ExamSession.tenant_id, tenant_id)).to_list()
    if selected_year:
        exam_sessions = [s for s in exam_sessions if s.academic_year_label == selected_year]
    session_ids = [s.id for s in exam_sessions]

    user_dept: dict[PydanticObjectId, PydanticObjectId | None] = {}
    for profile in profiles:
        user_dept[profile.user_id] = profile.department_id

    pass_stats: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    if session_ids:
        results = await ExamStudentSubjectResult.find(
            Eq(ExamStudentSubjectResult.tenant_id, tenant_id),
            In(ExamStudentSubjectResult.exam_session_id, session_ids),
        ).to_list()
        for row in results:
            dept_id = user_dept.get(row.student_user_id)
            if dept_id is None or dept_id not in dept_ids:
                continue
            key = str(dept_id)
            if row.outcome == ExamSubjectResultOutcome.PASS:
                pass_stats[key][0] += 1
            elif row.outcome == ExamSubjectResultOutcome.FAIL:
                pass_stats[key][1] += 1

    pass_rates: list[float] = []
    dept_pass_rate: dict[str, float] = {}
    for dept in departments:
        did = str(dept.id)
        passed, failed = pass_stats.get(did, [0, 0])
        total_results = passed + failed
        if total_results:
            rate = round((passed / total_results) * 100, 1)
            pass_rates.append(rate)
            dept_pass_rate[did] = rate
    college_pass_avg = round(mean(pass_rates), 1) if pass_rates else None

    attention_rows: list[DepartmentAttentionTableRow] = []
    for dept in departments:
        did = str(dept.id)
        if did in acting_heads:
            attention_rows.append(
                DepartmentAttentionTableRow(
                    department_id=did,
                    department_name=dept.name,
                    issue="HoD position held in acting capacity",
                    owner_label="Principal",
                    status_code="open",
                    status_label="Open",
                    status_tone="warning",
                    detail_href=f"/college-admin/organization/department-head-assignment?departmentId={did}",
                )
            )
        elif not dept.head_user_id:
            attention_rows.append(
                DepartmentAttentionTableRow(
                    department_id=did,
                    department_name=dept.name,
                    issue="Head of department not assigned",
                    owner_label="Principal",
                    status_code="open",
                    status_label="Open",
                    status_tone="warning",
                    detail_href=f"/college-admin/organization/department-head-assignment?departmentId={did}",
                )
            )

    for dept in departments:
        did = str(dept.id)
        rate = dept_pass_rate.get(did)
        if college_pass_avg is not None and rate is not None and rate < college_pass_avg:
            hod = head_names.get(dept.head_user_id, "HoD") if dept.head_user_id else "Academic office"
            attention_rows.append(
                DepartmentAttentionTableRow(
                    department_id=did,
                    department_name=dept.name,
                    issue="Pass rate below college average",
                    owner_label=hod,
                    status_code="review",
                    status_label="Review",
                    status_tone="error",
                    detail_href=f"/college-admin/organization/department-details?departmentId={did}",
                )
            )

    for dept_id, vac in sorted(vacancies_by_dept.items(), key=lambda x: -x[1]):
        if vac <= 0:
            continue
        dept = next((d for d in departments if str(d.id) == dept_id), None)
        if not dept:
            continue
        attention_rows.append(
            DepartmentAttentionTableRow(
                department_id=dept_id,
                department_name=dept.name,
                issue=f"{vac} faculty position{'s' if vac != 1 else ''} vacant",
                owner_label="HR Office",
                status_code="hiring",
                status_label="Hiring",
                status_tone="warning",
                detail_href="/college-admin/organization/department-faculty-allocation",
            )
        )

    attention_rows = attention_rows[:_MAX_ATTENTION_ROWS]
    open_items = len(attention_rows)

    total_for_schools = dept_count or 1
    school_bars: list[DepartmentSchoolBarItem] = []
    for unit in sorted(school_units, key=lambda u: u.name):
        count = sum(1 for d in departments if d.organization_unit_id == unit.id)
        if school_oid is not None and unit.id != school_oid:
            continue
        school_bars.append(
            DepartmentSchoolBarItem(
                school_id=str(unit.id),
                school_name=unit.name,
                department_count=count,
                share_percent=int(round(100 * count / total_for_schools)) if count else 0,
            )
        )
    unassigned = sum(1 for d in departments if not d.organization_unit_id)
    if unassigned and school_oid is None:
        school_bars.append(
            DepartmentSchoolBarItem(
                school_id="",
                school_name="Unassigned",
                department_count=unassigned,
                share_percent=int(round(100 * unassigned / total_for_schools)),
            )
        )
    school_bars.sort(key=lambda row: row.department_count, reverse=True)

    quick_actions = [
        DepartmentQuickActionItem(
            key="assign_head",
            title="Assign department head",
            subtitle=f"{vacant_heads} vacanc{'ies' if vacant_heads != 1 else 'y'}",
            action_label="Assign →",
            href="/college-admin/organization/department-head-assignment",
            icon_slug="user-cog",
        ),
        DepartmentQuickActionItem(
            key="map_programmes",
            title="Map programmes to departments",
            subtitle=f"{len(unmapped_programmes)} unmapped programme{'s' if len(unmapped_programmes) != 1 else ''}",
            action_label="Map →",
            href="/college-admin/organization/programme-course-mapping",
            icon_slug="git-branch",
        ),
        DepartmentQuickActionItem(
            key="allocate_faculty",
            title="Allocate faculty",
            subtitle=f"{vacancy_total} vacanc{'ies' if vacancy_total != 1 else 'y'}",
            action_label="Allocate →",
            href="/college-admin/organization/department-faculty-allocation",
            icon_slug="users",
        ),
    ]

    years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-start_date").to_list()
    year_options = [UserDashboardFilterOption(value="", label="Current year")]
    for year in years:
        label = year.label or str(year.start_date.year)
        year_options.append(UserDashboardFilterOption(value=label, label=label))
    seen_year_labels: set[str] = set()
    deduped_year_options = [year_options[0]]
    for opt in year_options[1:]:
        if opt.label not in seen_year_labels:
            seen_year_labels.add(opt.label)
            deduped_year_options.append(opt)
    if selected_year and selected_year not in seen_year_labels and selected_year not in {"", year_label}:
        deduped_year_options.insert(1, UserDashboardFilterOption(value=selected_year, label=selected_year))

    campuses = await list_campuses(scope, active_only=False)
    campus_options = [UserDashboardFilterOption(value="", label="All campuses")]
    for campus in sorted(campuses, key=lambda c: c.name):
        campus_options.append(UserDashboardFilterOption(value=campus.campus_id, label=campus.name))

    school_options = [UserDashboardFilterOption(value="", label="All schools")]
    for unit in sorted(school_units, key=lambda u: u.name):
        school_options.append(UserDashboardFilterOption(value=str(unit.id), label=unit.name))

    updated_label = as_utc_aware(utcnow()).astimezone(_IST).strftime("%H:%M") + " IST"

    return DepartmentManagementDashboardPageRead(
        page_title="Department Management Dashboard",
        page_subtitle="Departments, heads, programmes and staffing at a glance",
        export_label="Export",
        create_department_label="Create department",
        create_department_href="/college-admin/organization/create-department",
        academic_year_filter_label="Academic year",
        campus_filter_label="Campus",
        school_filter_label="School",
        scope_indicator_label="College scope",
        updated_at_label=updated_label,
        academic_year_options=deduped_year_options,
        campus_options=campus_options,
        school_options=school_options,
        selected_academic_year=selected_year or "",
        selected_campus_id=campus_id or "",
        selected_school_id=school_id or "",
        kpis=kpis,
        enrollment_chart_title="Students and faculty by department",
        enrollment_bars=enrollment_bars,
        attention_section_title="Departments needing attention",
        attention_table_headers=["Department", "Issue", "Owner", "Status"],
        attention_rows=attention_rows,
        attention_footer_label=f"{open_items} open item{'s' if open_items != 1 else ''}",
        attention_view_all_href="/college-admin/organization/all-departments",
        attention_view_all_label="View all →",
        schools_section_title="Departments by school",
        school_bars=school_bars,
        quick_actions_title="Quick actions",
        quick_actions=quick_actions,
        footer_disclaimer=(
            "Live institutional data · Departments, staffing and academic records · All times IST"
        ),
        footer_snapshot_label="Live snapshot",
        generated_at=utcnow(),
    )