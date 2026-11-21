"""Academic configuration overview dashboard (CA 05.01)."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import as_utc_aware, utcnow
from app.modules.academics.curriculum_models import CourseRecord, EnrollmentRosterEntry, SectionOffering
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import (
    AcademicConfigurationVersion,
    AcademicProgramme,
    AcademicRegulation,
    AcademicTerm,
    AcademicYear,
    ConfigPublicationStatus,
)
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AcademicConfigAreaTableRow,
    AcademicConfigSetupAlert,
    AcademicConfigShortcutItem,
    AcademicConfigurationDashboardPageRead,
    AcademicRegulationUsageItem,
    UserDashboardKpi,
)
from app.modules.examinations.models import GradingPolicy
from app.modules.students.curriculum_models import CurriculumReference
from app.modules.students.models import StudentProfile

_IST = ZoneInfo("Asia/Kolkata")
_reader = OperationalDataReader()

_AREA_ORDER: list[tuple[str, str, str]] = [
    ("academic_years", "Academic years & semesters", "/college-admin/academics/academic-year-management"),
    ("programmes", "Programmes & intake", "/college-admin/academics/programme-management"),
    ("curriculum", "Curriculum", "/college-admin/academics/curriculum-management"),
    ("course_offerings", "Course offerings", "/college-admin/academics/course-configuration"),
    ("batch_sections", "Batch & section allocation", "/college-admin/academics/batch-section-configuration"),
    ("grading", "Grading scheme", "/college-admin/academics/grading-system-configuration"),
]


def _fmt_date(value: date | None) -> str:
    if value is None:
        return "—"
    return value.strftime("%d %b %Y")


def _fmt_datetime_label(dt) -> str:
    if dt is None:
        return "—"
    aware = as_utc_aware(dt)
    return aware.astimezone(_IST).strftime("%d %b %Y")


def _status_from_progress(progress: int) -> tuple[str, str, str]:
    if progress >= 100:
        return "complete", "Complete", "success"
    if progress > 0:
        return "in_progress", "In progress", "warning"
    return "not_started", "Not started", "muted"


def _week_in_term(term: AcademicTerm | None, today: date) -> int | None:
    if term is None or term.start_date is None:
        return None
    if term.end_date and today > term.end_date:
        return None
    if today < term.start_date:
        return None
    return max(1, (today - term.start_date).days // 7 + 1)


async def _load_user_names(user_ids: set[PydanticObjectId]) -> dict[PydanticObjectId, str]:
    if not user_ids:
        return {}
    users = await User.find(In(User.id, list(user_ids))).to_list()
    return {user.id: user.full_name for user in users if user.id is not None}


async def _owner_label(
    *,
    tenant_id: PydanticObjectId,
    names: dict[PydanticObjectId, str],
    user_id: PydanticObjectId | None,
    fallback_scope: str | None = None,
) -> str:
    if user_id and user_id in names:
        return names[user_id]
    if fallback_scope:
        version = (
            await AcademicConfigurationVersion.find(
                Eq(AcademicConfigurationVersion.tenant_id, tenant_id),
                Eq(AcademicConfigurationVersion.scope, fallback_scope),
            )
            .sort("-version_number")
            .limit(1)
            .first_or_none()
        )
        if version and version.published_by and version.published_by in names:
            return names[version.published_by]
        if version and version.published_by:
            user = await User.get(version.published_by)
            if user:
                return user.full_name
    return "Not assigned"


def _grading_scheme_label(policy: GradingPolicy | None, regulation: AcademicRegulation | None) -> str:
    if regulation and regulation.rules:
        label = regulation.rules.get("scheme_label") or regulation.rules.get("label")
        if isinstance(label, str) and label.strip():
            return label.strip()
    if policy and policy.grade_bands:
        return f"{len(policy.grade_bands)}-band scale"
    return "Grading policy"


async def get_academic_configuration_dashboard_page(
    scope: AccessScope,
) -> AcademicConfigurationDashboardPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_READ)
    tenant_id = require_college_tenant_scope(scope)
    today = utcnow().date()

    year_label, semester_label = await _reader.current_academic_term(tenant_id)

    years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-year_code").to_list()
    current_year = next((y for y in years if y.is_current), years[0] if years else None)
    terms = await AcademicTerm.find(Eq(AcademicTerm.tenant_id, tenant_id)).to_list()
    current_term = next((t for t in terms if t.is_current), None)
    if current_term is None and current_year is not None:
        year_terms = [t for t in terms if t.academic_year_id == current_year.id]
        current_term = year_terms[0] if year_terms else None

    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    active_programmes = [p for p in programmes if p.is_active]
    courses = await CourseRecord.find(Eq(CourseRecord.tenant_id, tenant_id), Eq(CourseRecord.is_active, True)).to_list()
    curriculum_refs = await CurriculumReference.find(Eq(CurriculumReference.tenant_id, tenant_id)).to_list()
    offerings = await SectionOffering.find(Eq(SectionOffering.tenant_id, tenant_id)).to_list()
    rosters = await EnrollmentRosterEntry.find(Eq(EnrollmentRosterEntry.tenant_id, tenant_id)).to_list()
    regulations = await AcademicRegulation.find(Eq(AcademicRegulation.tenant_id, tenant_id)).to_list()
    grading_reg = next((r for r in regulations if r.scope_key == "grading"), None)
    grading_policy = await GradingPolicy.find_one(Eq(GradingPolicy.tenant_id, tenant_id))
    students = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()

    selected_year_label = (current_year.label if current_year else year_label) or "—"
    selected_semester = (current_term.label if current_term else semester_label) or "—"
    week_no = _week_in_term(current_term, today)

    user_ids: set[PydanticObjectId] = set()
    if current_year and current_year.updated_by:
        user_ids.add(current_year.updated_by)
    for reg in regulations:
        if reg.updated_by:
            user_ids.add(reg.updated_by)
    user_names = await _load_user_names(user_ids)

    # --- area progress ---
    terms_for_current = (
        [t for t in terms if current_year and t.academic_year_id == current_year.id] if current_year else []
    )
    published_term_count = sum(1 for t in terms_for_current if t.status == ConfigPublicationStatus.PUBLISHED)
    years_progress = 0
    if current_year:
        if current_year.status == ConfigPublicationStatus.PUBLISHED:
            years_progress += 50
        if published_term_count >= 1:
            years_progress += 25
        if published_term_count >= 2:
            years_progress += 25
    years_updated = max(
        [current_year.updated_at if current_year else utcnow(), *[t.updated_at for t in terms_for_current]],
        default=utcnow(),
    )
    years_owner = await _owner_label(
        tenant_id=tenant_id,
        names=user_names,
        user_id=current_year.updated_by if current_year else None,
        fallback_scope="academic_year",
    )

    programme_total = len(active_programmes)
    programme_configured = sum(
        1
        for p in active_programmes
        if p.status == ConfigPublicationStatus.PUBLISHED and p.department_id is not None
    )
    programmes_progress = round(programme_configured / programme_total * 100) if programme_total else 0
    prog_updated = max((p.updated_at for p in active_programmes), default=utcnow())
    programmes_owner = await _owner_label(
        tenant_id=tenant_id,
        names=user_names,
        user_id=None,
        fallback_scope="academic_programme",
    )

    prog_codes = {p.programme_code.upper() for p in active_programmes}
    refs_for_year = [
        r
        for r in curriculum_refs
        if (
            selected_year_label in {"—", "", None}
            or r.academic_year_label == selected_year_label
        )
        and r.programme_code.upper() in prog_codes
    ]
    curriculum_programmes = {r.programme_code.upper() for r in refs_for_year}
    curriculum_progress = round(len(curriculum_programmes) / programme_total * 100) if programme_total else 0
    curriculum_updated = max((r.updated_at for r in refs_for_year), default=utcnow())
    regulation_titles = sorted(
        {r.academic_regulations[0] for r in refs_for_year if r.academic_regulations},
    )
    curriculum_label = (
        f"Curriculum — {regulation_titles[0]}"
        if len(regulation_titles) == 1
        else "Curriculum"
    )
    curriculum_owner = await _owner_label(
        tenant_id=tenant_id,
        names=user_names,
        user_id=None,
        fallback_scope="curriculum",
    )

    term_offerings = [
        o
        for o in offerings
        if o.academic_year_label == selected_year_label and o.semester_label == selected_semester
    ]
    course_by_code = {c.course_code.upper(): c for c in courses}
    dept_ids_with_programmes = {p.department_id for p in active_programmes if p.department_id}
    depts_with_offerings: set[PydanticObjectId] = set()
    for offering in term_offerings:
        course = course_by_code.get(offering.course_code.upper())
        if course and course.department_id:
            depts_with_offerings.add(course.department_id)
    if dept_ids_with_programmes:
        offerings_progress = round(len(depts_with_offerings) / len(dept_ids_with_programmes) * 100)
    else:
        offerings_progress = 100 if term_offerings else 0
    offerings_updated = max((c.updated_at for c in courses), default=utcnow())
    offerings_owner = await _owner_label(
        tenant_id=tenant_id,
        names=user_names,
        user_id=None,
        fallback_scope="course",
    )

    term_rosters = [
        r
        for r in rosters
        if r.academic_year_label == selected_year_label and r.semester_label == selected_semester
    ]
    roster_keys = {(r.course_id, r.section_code) for r in term_rosters}
    offering_keys = {(o.course_id, o.section_code) for o in term_offerings}
    if offering_keys:
        batch_progress = min(100, round(len(roster_keys) / len(offering_keys) * 100))
    elif term_rosters:
        batch_progress = 100
    else:
        batch_progress = 0
    batch_updated = prog_updated if term_rosters or term_offerings else utcnow()
    batch_owner = await _owner_label(
        tenant_id=tenant_id,
        names=user_names,
        user_id=None,
        fallback_scope="section",
    )

    grading_progress = 0
    if grading_reg and grading_reg.status == ConfigPublicationStatus.PUBLISHED:
        grading_progress += 70
    if grading_policy and grading_policy.grade_bands:
        grading_progress += 30
    grading_progress = min(100, grading_progress)
    grading_updated = (
        grading_reg.updated_at
        if grading_reg
        else (grading_policy.updated_at if grading_policy else utcnow())
    )
    grading_owner = await _owner_label(
        tenant_id=tenant_id,
        names=user_names,
        user_id=grading_reg.updated_by if grading_reg else None,
        fallback_scope="regulation_grading",
    )

    progress_by_key = {
        "academic_years": years_progress,
        "programmes": programmes_progress,
        "curriculum": curriculum_progress,
        "course_offerings": offerings_progress,
        "batch_sections": batch_progress,
        "grading": grading_progress,
    }
    updated_by_key = {
        "academic_years": years_updated,
        "programmes": prog_updated,
        "curriculum": curriculum_updated,
        "course_offerings": offerings_updated,
        "batch_sections": batch_updated,
        "grading": grading_updated,
    }
    owner_by_key = {
        "academic_years": years_owner,
        "programmes": programmes_owner,
        "curriculum": curriculum_owner,
        "course_offerings": offerings_owner,
        "batch_sections": batch_owner,
        "grading": grading_owner,
    }
    label_overrides = {"curriculum": curriculum_label}

    config_rows: list[AcademicConfigAreaTableRow] = []
    for area_key, default_label, href in _AREA_ORDER:
        progress = progress_by_key[area_key]
        status_code, status_label, status_tone = _status_from_progress(progress)
        config_rows.append(
            AcademicConfigAreaTableRow(
                area_key=area_key,
                area_label=label_overrides.get(area_key, default_label),
                owner_label=owner_by_key[area_key],
                last_updated_label=_fmt_datetime_label(updated_by_key[area_key]),
                progress_percent=progress,
                status_code=status_code,
                status_label=status_label,
                status_tone=status_tone,
                detail_href=href,
            )
        )

    pending_areas = [row for row in config_rows if row.progress_percent < 100]
    pending_count = len(pending_areas)

    prog_with_regulation = 0
    for code in prog_codes:
        refs = [r for r in curriculum_refs if r.programme_code.upper() == code and r.academic_regulations]
        if refs:
            prog_with_regulation += 1
    regulation_hint = (
        "All have active regulation"
        if programme_total and prog_with_regulation >= programme_total
        else f"{prog_with_regulation} of {programme_total} with regulation"
        if programme_total
        else "No programmes configured yet"
    )
    regulation_tone = "success" if programme_total and prog_with_regulation >= programme_total else "muted"

    term_hint_parts = [selected_semester]
    if week_no is not None:
        term_hint_parts.append(f"week {week_no}")
    term_hint = " · ".join(term_hint_parts) if selected_semester != "—" else "No active term"

    offerings_hint = (
        f"{len(term_offerings)} offerings this semester"
        if term_offerings
        else "No offerings for current term"
    )

    pending_hint = (
        f"{pending_count} area{'s' if pending_count != 1 else ''} incomplete"
        if pending_count
        else "All configuration areas complete"
    )
    pending_tone = "warning" if pending_count else "success"

    kpis = [
        UserDashboardKpi(
            key="current_academic_year",
            label="Current academic year",
            value=selected_year_label,
            hint_line=term_hint,
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="programmes_configured",
            label="Programmes configured",
            value=f"{programme_configured} / {programme_total}" if programme_total else "0",
            hint_line=regulation_hint,
            hint_tone=regulation_tone,
        ),
        UserDashboardKpi(
            key="courses_defined",
            label="Courses defined",
            value=f"{len(courses):,}",
            hint_line=offerings_hint,
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="pending_configuration",
            label="Pending configuration",
            value=str(pending_count),
            hint_line=pending_hint,
            hint_tone=pending_tone,
        ),
    ]

    setup_alert: AcademicConfigSetupAlert | None = None
    if pending_areas:
        focus = min(pending_areas, key=lambda row: row.progress_percent)
        incomplete_dept_count = len(dept_ids_with_programmes - depts_with_offerings)
        detail_bits: list[str] = []
        if focus.area_key == "course_offerings" and incomplete_dept_count:
            detail_bits.append(
                f"Course offerings for {incomplete_dept_count} department{'s' if incomplete_dept_count != 1 else ''}",
            )
        if focus.area_key == "batch_sections" and batch_progress < 100:
            detail_bits.append("Section allocation is still pending")
        if not detail_bits:
            detail_bits.append(f"{focus.area_label} is {focus.progress_percent}% complete")
        deadline_label: str | None = None
        if current_term and current_term.end_date:
            deadline_label = _fmt_date(current_term.end_date)
        elif current_year and current_year.end_date:
            deadline_label = _fmt_date(current_year.end_date)
        setup_alert = AcademicConfigSetupAlert(
            title=f"{selected_semester} setup is {focus.progress_percent}% complete",
            description=" · ".join(detail_bits) + (f". Deadline {deadline_label}." if deadline_label else "."),
            continue_label="Continue setup →",
            continue_href=focus.detail_href,
            deadline_label=deadline_label,
        )

    prog_regulation_map: dict[str, str] = {}
    for ref in curriculum_refs:
        if ref.academic_regulations:
            prog_regulation_map[ref.programme_code.upper()] = ref.academic_regulations[0]

    reg_counts: dict[str, int] = defaultdict(int)
    for student in students:
        code = (student.programme_code or "").upper()
        reg_key = prog_regulation_map.get(code, "Unassigned")
        reg_counts[reg_key] += 1

    total_students = sum(reg_counts.values())
    sorted_regs = sorted(reg_counts.items(), key=lambda item: (-item[1], item[0]))
    current_reg = sorted_regs[0][0] if sorted_regs else None
    regulation_items: list[AcademicRegulationUsageItem] = []
    for reg_key, count in sorted_regs[:5]:
        share = round(count / total_students * 100) if total_students else 0
        if reg_key == current_reg and count > 0:
            tone = "current"
            label = f"{reg_key} (current)" if reg_key != "Unassigned" else reg_key
        elif count > 0 and len(sorted_regs) > 1 and reg_key == sorted_regs[-1][0] and share <= 10:
            tone = "phasing_out"
            label = f"{reg_key} (phasing out)" if reg_key != "Unassigned" else reg_key
        else:
            tone = "active"
            label = reg_key
        regulation_items.append(
            AcademicRegulationUsageItem(
                regulation_key=reg_key,
                regulation_label=label,
                student_count=count,
                share_percent=share,
                tone=tone,
            )
        )

    curriculum_count = len({r.programme_code.upper() for r in curriculum_refs})
    scheme_label = _grading_scheme_label(grading_policy, grading_reg)
    shortcuts = [
        AcademicConfigShortcutItem(
            key="academic_year",
            title="Academic year management",
            subtitle=selected_year_label,
            action_label="Open →",
            href="/college-admin/academics/academic-year-management",
            icon_slug="calendar-days",
        ),
        AcademicConfigShortcutItem(
            key="curriculum",
            title="Curriculum management",
            subtitle=f"{curriculum_count} curricula",
            action_label="Open →",
            href="/college-admin/academics/curriculum-management",
            icon_slug="book-open",
        ),
        AcademicConfigShortcutItem(
            key="grading",
            title="Grading system",
            subtitle=scheme_label,
            action_label="Open →",
            href="/college-admin/academics/grading-system-configuration",
            icon_slug="scale",
        ),
    ]

    generated = utcnow()
    snapshot = as_utc_aware(generated).astimezone(_IST).strftime("Sample snapshot · %d %b %Y, %H:%M IST")

    open_year_href = "/college-admin/academics/academic-year-management"
    if current_year:
        open_year_href = f"/college-admin/academics/academic-year-management?year_id={current_year.id}"

    return AcademicConfigurationDashboardPageRead(
        page_title="Academic Configuration Dashboard",
        page_subtitle="Status of academic years, programmes, curricula and grading rules",
        checklist_label="Configuration checklist",
        checklist_href="/college-admin/academics/academic-configuration-history",
        open_current_year_label="Open current year",
        open_current_year_href=open_year_href,
        kpis=kpis,
        setup_alert=setup_alert,
        config_section_title="Configuration status by area",
        config_table_headers=["Area", "Owner", "Last updated", "Progress", "Status"],
        config_area_rows=config_rows,
        config_footer_count_label=f"{len(config_rows)} configuration areas",
        config_checklist_href="/college-admin/academics/academic-configuration-history",
        config_checklist_label="View checklist →",
        regulations_section_title="Regulations in use",
        regulation_items=regulation_items,
        shortcuts_section_title="Shortcuts",
        shortcuts=shortcuts,
        footer_disclaimer="Live configuration data from your tenant · No sample student or finance records",
        footer_snapshot_label=snapshot,
        generated_at=generated,
    )