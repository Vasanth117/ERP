"""Semester management page (CA 05.03 – college admin academics)."""

from __future__ import annotations

from datetime import date
from uuid import uuid4
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.academics.curriculum_models import SectionOffering
from app.modules.attendance.enums import AttendanceSessionStatus
from app.modules.attendance.models import AttendanceSession
from app.modules.audit.service import record_audit
from app.modules.college_admin.academic_config_models import AcademicTerm, AcademicYear, ConfigPublicationStatus
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AcademicYearCreateFormOption,
    SemesterLinkedItem,
    SemesterManagementCreate,
    SemesterManagementPageRead,
    SemesterManagementSettingsSave,
    SemesterManagementTableRow,
    SemesterProgressItem,
    SemesterSettingsFieldMeta,
    SemesterSettingsForm,
)
from app.modules.college_admin.years_semesters_nav import years_semesters_sub_nav
from app.modules.examinations.exam_cell_enums import ExamSessionStatus
from app.modules.examinations.exam_cell_models import ExamSession

_IST = ZoneInfo("Asia/Kolkata")


def _fmt(value: date | None) -> str:
    if value is None:
        return "—"
    return value.strftime("%d %b %Y")


def _period_label(start: date | None, end: date | None) -> str:
    if start and end:
        return f"{start.strftime('%d %b')} – {end.strftime('%d %b %Y')}"
    if start:
        return f"{_fmt(start)} – —"
    return "—"


def _week_label(term: AcademicTerm, today: date) -> str:
    if term.start_date is None:
        return "—"
    if term.end_date and today > term.end_date:
        return "Ended"
    if today < term.start_date:
        return "Upcoming"
    week = max(1, (today - term.start_date).days // 7 + 1)
    return f"Week {week}"


def _term_status(term: AcademicTerm, today: date) -> tuple[str, str, str]:
    if term.is_current:
        return "current", "Current", "success"
    if term.end_date and term.end_date < today:
        return "completed", "Completed", "muted"
    if term.start_date and term.start_date > today:
        return "planned", "Planned", "info"
    if term.status == ConfigPublicationStatus.PUBLISHED:
        return "published", "Published", "info"
    return "in_progress", "In progress", "warning"


async def get_semester_management_page(
    scope: AccessScope,
    *,
    academic_year_id: str | None = None,
    term_id: str | None = None,
) -> SemesterManagementPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_READ)
    tenant_id = require_college_tenant_scope(scope)
    today = utcnow().date()

    years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-start_date").to_list()
    year_options = [AcademicYearCreateFormOption(value="", label="Select year")]
    for year in years:
        year_options.append(AcademicYearCreateFormOption(value=str(year.id), label=year.label))

    selected_year: AcademicYear | None = None
    if academic_year_id:
        selected_year = await AcademicYear.get(PydanticObjectId(academic_year_id))
        if selected_year is None or selected_year.tenant_id != tenant_id:
            selected_year = None
    if selected_year is None:
        selected_year = next((y for y in years if y.is_current), years[0] if years else None)

    terms: list[AcademicTerm] = []
    if selected_year:
        terms = await AcademicTerm.find(
            Eq(AcademicTerm.tenant_id, tenant_id),
            Eq(AcademicTerm.academic_year_id, selected_year.id),
        ).sort("+term_code").to_list()

    offerings = (
        await SectionOffering.find(Eq(SectionOffering.tenant_id, tenant_id)).to_list()
        if selected_year
        else []
    )

    rows: list[SemesterManagementTableRow] = []
    for term in terms:
        year_label = selected_year.label if selected_year else ""
        course_count = sum(
            1
            for o in offerings
            if o.academic_year_label == year_label and o.semester_label == term.label
        )
        code, label, tone = _term_status(term, today)
        rows.append(
            SemesterManagementTableRow(
                term_id=str(term.id),
                label=term.label,
                period_label=_period_label(term.start_date, term.end_date),
                week_label=_week_label(term, today),
                course_count=course_count,
                status_code=code,
                status_label=label,
                status_tone=tone,
                is_current=term.is_current,
            )
        )

    selected_term: AcademicTerm | None = None
    if term_id:
        selected_term = await AcademicTerm.get(PydanticObjectId(term_id))
        if selected_term is None or selected_term.tenant_id != tenant_id:
            selected_term = None
    if selected_term is None:
        selected_term = next((t for t in terms if t.is_current), terms[0] if terms else None)

    settings_form: SemesterSettingsForm | None = None
    panel_title = "Semester settings"
    if selected_term:
        panel_title = f"{selected_term.label} settings"
        settings_form = SemesterSettingsForm(
            teaching_starts=selected_term.start_date,
            last_instruction_day=selected_term.last_instruction_day,
            mid_semester_exam_date=selected_term.mid_semester_exam_date,
            end_semester_exam_date=selected_term.end_semester_exam_date,
            course_registration_opens=selected_term.course_registration_opens,
            add_drop_deadline=selected_term.add_drop_deadline,
        )

    progress: list[SemesterProgressItem] = []
    linked: list[SemesterLinkedItem] = []
    if selected_term and selected_year:
        year_label = selected_year.label
        sem_label = selected_term.label
        offerings_count = sum(
            1 for o in offerings if o.academic_year_label == year_label and o.semester_label == sem_label
        )
        offering_target = max(len(terms), 1)
        offerings_pct = min(100, round(offerings_count / offering_target * 100)) if offering_target else 0
        reg_fields = [selected_term.course_registration_opens, selected_term.add_drop_deadline]
        reg_pct = 100 if all(reg_fields) else (50 if any(reg_fields) else 0)
        exam_pct = 100 if selected_term.mid_semester_exam_date and selected_term.end_semester_exam_date else (
            50 if selected_term.mid_semester_exam_date or selected_term.end_semester_exam_date else 0
        )
        progress = [
            SemesterProgressItem(key="offerings", label="Course offerings configured", progress_percent=offerings_pct),
            SemesterProgressItem(key="registration", label="Registration window set", progress_percent=reg_pct),
            SemesterProgressItem(key="exams", label="Exam schedule linked", progress_percent=exam_pct),
        ]

        exam_sessions = await ExamSession.find(
            Eq(ExamSession.tenant_id, tenant_id),
            Eq(ExamSession.academic_year_label, year_label),
            Eq(ExamSession.semester_label, sem_label),
        ).to_list()
        if exam_sessions:
            latest = sorted(exam_sessions, key=lambda s: s.examination_end_at, reverse=True)[0]
            exam_status = latest.status.value.replace("_", " ").title()
            tone = "success" if latest.status == ExamSessionStatus.PUBLISHED else "warning"
            linked.append(
                SemesterLinkedItem(
                    key="exams",
                    title="End-semester exams",
                    subtitle=latest.name,
                    status_label=exam_status,
                    status_tone=tone,
                )
            )
        else:
            linked.append(
                SemesterLinkedItem(
                    key="exams",
                    title="End-semester exams",
                    subtitle="No examination session yet",
                    status_label="Not scheduled",
                    status_tone="muted",
                )
            )

        att_pending = await AttendanceSession.find(
            Eq(AttendanceSession.tenant_id, tenant_id),
            Eq(AttendanceSession.academic_year_label, year_label),
            Eq(AttendanceSession.semester_label, sem_label),
            Eq(AttendanceSession.status, AttendanceSessionStatus.DRAFT),
        ).count()
        linked.append(
            SemesterLinkedItem(
                key="attendance",
                title="Attendance submission",
                subtitle=f"{att_pending} sessions pending" if att_pending else "All sessions submitted",
                status_label="On track" if att_pending == 0 else "Pending",
                status_tone="success" if att_pending == 0 else "warning",
            )
        )

    generated = utcnow()
    snapshot = as_utc_aware(generated).astimezone(_IST).strftime("Sample snapshot · %d %b %Y, %H:%M IST")

    return SemesterManagementPageRead(
        page_title="Semester Management",
        page_subtitle="Configure semesters, teaching periods and academic milestones",
        export_label="Export",
        new_semester_label="New semester",
        year_filter_options=year_options,
        selected_academic_year_id=str(selected_year.id) if selected_year else None,
        selected_academic_year_label=selected_year.label if selected_year else "—",
        semesters_panel_title=f"Semesters in {selected_year.label}" if selected_year else "Semesters",
        table_headers=["Semester", "Period", "Week", "Courses", "Status"],
        semester_rows=rows,
        semester_count_label=f"{len(rows)} semester{'s' if len(rows) != 1 else ''}",
        manage_terms_href="/college-admin/academics/semester-management",
        manage_terms_label="Manage terms →",
        selected_term_id=str(selected_term.id) if selected_term else None,
        settings_panel_title=panel_title,
        settings_form=settings_form,
        settings_field_meta=[
            SemesterSettingsFieldMeta(key="teaching_starts", label="Teaching starts", required=True),
            SemesterSettingsFieldMeta(key="last_instruction_day", label="Last instruction day", required=True),
            SemesterSettingsFieldMeta(key="mid_semester_exam_date", label="Mid-semester exams"),
            SemesterSettingsFieldMeta(key="end_semester_exam_date", label="End-semester exams", required=True),
            SemesterSettingsFieldMeta(key="course_registration_opens", label="Course registration window"),
            SemesterSettingsFieldMeta(key="add_drop_deadline", label="Add / drop deadline"),
        ],
        save_label="Save semester settings",
        cancel_label="Cancel",
        settings_form_note="Changes are saved to the audit log with your name and time.",
        progress_section_title="Semester progress",
        progress_items=progress,
        linked_section_title="Linked items",
        linked_items=linked,
        sub_nav=years_semesters_sub_nav(active="semesters"),
        years_button_label="Years",
        years_button_href="/college-admin/academics/academic-year-management",
        footer_disclaimer="Live academic configuration · Semesters and milestones · All times IST",
        footer_snapshot_label=snapshot,
        generated_at=generated,
    )


async def save_semester_management_settings(
    scope: AccessScope,
    payload: SemesterManagementSettingsSave,
) -> SemesterManagementPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    term_id = to_object_id(payload.term_id, "term_id")
    term = await AcademicTerm.get(term_id)
    if term is None or term.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Semester not found", status_code=404)

    year = await AcademicYear.get(term.academic_year_id)
    if year and year.status == ConfigPublicationStatus.ARCHIVED:
        raise AppError(code="FORBIDDEN", message="Closed years are locked", status_code=403)

    form = payload.settings
    term.start_date = form.teaching_starts
    term.end_date = form.end_semester_exam_date or term.end_date
    term.last_instruction_day = form.last_instruction_day
    term.mid_semester_exam_date = form.mid_semester_exam_date
    term.end_semester_exam_date = form.end_semester_exam_date
    term.course_registration_opens = form.course_registration_opens
    term.add_drop_deadline = form.add_drop_deadline
    term.updated_at = utcnow()
    await term.save()

    await record_audit(
        actor_id=scope.user_id,
        action="academic.term.settings.saved",
        resource_type="academic_term",
        resource_id=str(term.id),
        tenant_id=tenant_id,
    )
    return await get_semester_management_page(
        scope,
        academic_year_id=str(term.academic_year_id),
        term_id=str(term.id),
    )


async def create_semester_management_term(
    scope: AccessScope,
    payload: SemesterManagementCreate,
) -> SemesterManagementPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    year_id = to_object_id(payload.academic_year_id, "academic_year_id")
    year = await AcademicYear.get(year_id)
    if year is None or year.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Academic year not found", status_code=404)

    code = (payload.term_code or payload.label).upper().replace(" ", "-")[:32]
    existing = await AcademicTerm.find_one(
        Eq(AcademicTerm.tenant_id, tenant_id),
        Eq(AcademicTerm.academic_year_id, year_id),
        Eq(AcademicTerm.term_code, code),
    )
    if existing:
        code = f"{code}-{uuid4().hex[:4].upper()}"

    doc = AcademicTerm(
        tenant_id=tenant_id,
        academic_year_id=year_id,
        term_code=code,
        label=payload.label.strip(),
    )
    await doc.insert()

    await record_audit(
        actor_id=scope.user_id,
        action="academic.term.created",
        resource_type="academic_term",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
    )
    return await get_semester_management_page(
        scope,
        academic_year_id=str(year_id),
        term_id=str(doc.id),
    )