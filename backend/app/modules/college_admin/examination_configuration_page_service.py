"""Examination session setup / configuration page (CA 09.02)."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.attendance.models import AttendancePolicyReference
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicYear
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    ExaminationConfigurationPageRead,
    ExaminationConfigurationSave,
    ExaminationSetupFieldMeta,
    ExaminationSetupFormValues,
    ExaminationSetupToggleRule,
    StudentAdminDashboardFilterOption,
)
from app.modules.examinations.exam_cell_enums import (
    ExamSessionLifecycleAction,
    ExamSessionStatus,
    ExamSessionType,
)
from app.modules.examinations.exam_cell_models import ExamSession, ExamSessionRegistrationRules
from app.modules.examinations.exam_cell_schemas import ExamSessionAcademicScopeInput, ExamSessionCreate, ExamSessionUpdate
from app.modules.examinations.exam_cell_session_service import (
    create_exam_session,
    transition_exam_session,
    update_exam_session,
)
from app.modules.examinations.exam_cell_schemas import ExamSessionTransitionRequest

_IST = ZoneInfo("Asia/Kolkata")

_TYPE_OPTIONS: list[tuple[ExamSessionType, str]] = [
    (ExamSessionType.REGULAR, "Regular"),
    (ExamSessionType.SPECIAL, "Internal"),
    (ExamSessionType.SUPPLEMENTARY, "Supplementary"),
    (ExamSessionType.ARREAR, "Arrear"),
]

_SEMESTER_OPTIONS = [
    StudentAdminDashboardFilterOption(value="Odd", label="Odd"),
    StudentAdminDashboardFilterOption(value="Even", label="Even"),
    StudentAdminDashboardFilterOption(value="Summer", label="Summer"),
]


def _fmt_date_input(value: datetime | None) -> str:
    if value is None:
        return ""
    return as_utc_aware(value).astimezone(_IST).date().isoformat()


def _parse_form_date(value: str) -> datetime:
    try:
        day = date.fromisoformat(value.strip()[:10])
    except ValueError as exc:
        raise AppError(code="VALIDATION", message="Invalid date in form", status_code=422) from exc
    local = datetime(day.year, day.month, day.day, tzinfo=_IST)
    return local.astimezone(timezone.utc)


async def _academic_year_options(tenant_id: PydanticObjectId) -> list[StudentAdminDashboardFilterOption]:
    years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-start_date").to_list()
    if not years:
        return []
    return [StudentAdminDashboardFilterOption(value=row.label, label=row.label) for row in years]


async def _default_academic_year(tenant_id: PydanticObjectId) -> str:
    years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-start_date").to_list()
    for row in years:
        if row.is_current:
            return row.label
    return years[0].label if years else ""


async def _attendance_minimum_label(tenant_id: PydanticObjectId) -> str:
    policy = await AttendancePolicyReference.find_one(
        Eq(AttendancePolicyReference.tenant_id, tenant_id),
        Eq(AttendancePolicyReference.is_active, True),
    )
    pct = policy.rules.min_percentage_required if policy else 75.0
    return f"{pct:g}% minimum"


async def _toggle_rules_for_session(
    tenant_id: PydanticObjectId,
    exam_session_id: PydanticObjectId | None,
    *,
    attendance_hint: str,
) -> list[ExaminationSetupToggleRule]:
    rules_doc: ExamSessionRegistrationRules | None = None
    if exam_session_id is not None:
        rules_doc = await ExamSessionRegistrationRules.find_one(
            Eq(ExamSessionRegistrationRules.tenant_id, tenant_id),
            Eq(ExamSessionRegistrationRules.exam_session_id, exam_session_id),
        )
    block_unpaid = rules_doc.block_unpaid_students if rules_doc else True
    block_attendance = rules_doc.block_below_attendance if rules_doc else True
    allow_late = rules_doc.allow_late_registration if rules_doc else False
    return [
        ExaminationSetupToggleRule(
            key="block_unpaid_students",
            label="Block unpaid students",
            description="Fee clearance required",
            enabled=block_unpaid,
        ),
        ExaminationSetupToggleRule(
            key="block_below_attendance",
            label="Block below attendance",
            description=attendance_hint,
            enabled=block_attendance,
        ),
        ExaminationSetupToggleRule(
            key="allow_late_registration",
            label="Allow late registration",
            description="Late fee applies",
            enabled=allow_late,
        ),
    ]


def _field_meta() -> list[ExaminationSetupFieldMeta]:
    return [
        ExaminationSetupFieldMeta(key="session_name", label="Session name", required=True, field_type="text"),
        ExaminationSetupFieldMeta(key="examination_type", label="Type", required=True, field_type="select"),
        ExaminationSetupFieldMeta(key="academic_year_label", label="Academic year", required=True, field_type="select"),
        ExaminationSetupFieldMeta(key="semester_label", label="Semester group", required=True, field_type="select"),
        ExaminationSetupFieldMeta(key="examination_start_at", label="Start date", required=True, field_type="date"),
        ExaminationSetupFieldMeta(key="examination_end_at", label="End date", required=True, field_type="date"),
        ExaminationSetupFieldMeta(
            key="registration_end_at", label="Registration closes", required=True, field_type="date"
        ),
        ExaminationSetupFieldMeta(key="result_target_at", label="Result target", required=True, field_type="date"),
    ]


async def get_examination_configuration_page(
    scope: AccessScope,
    *,
    session_id: str | None = None,
    mode: str | None = None,
) -> ExaminationConfigurationPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    is_new = mode == "new" or not session_id
    attendance_hint = await _attendance_minimum_label(tenant_id)
    year_options = await _academic_year_options(tenant_id)
    type_options = [
        StudentAdminDashboardFilterOption(value=kind.value, label=label) for kind, label in _TYPE_OPTIONS
    ]

    session: ExamSession | None = None
    if session_id:
        session = await ExamSession.find_one(
            Eq(ExamSession.tenant_id, tenant_id),
            Eq(ExamSession.session_id, session_id),
        )
        if session is None:
            raise AppError(code="NOT_FOUND", message="Examination session not found", status_code=404)
        is_new = False

    if session:
        form = ExaminationSetupFormValues(
            session_name=session.name,
            examination_type=session.examination_type.value,
            academic_year_label=session.academic_year_label,
            semester_label=session.semester_label,
            examination_start_at=_fmt_date_input(session.examination_start_at),
            examination_end_at=_fmt_date_input(session.examination_end_at),
            registration_end_at=_fmt_date_input(session.registration_end_at),
            result_target_at=_fmt_date_input(session.result_processing_deadline_at),
        )
        page_subtitle = f"Create Examination · {session.name}"
        toggles = await _toggle_rules_for_session(tenant_id, session.id, attendance_hint=attendance_hint)
        continue_href = f"/college-admin/examinations/exam-configuration?session_id={session.session_id}"
    else:
        default_year = await _default_academic_year(tenant_id)
        form = ExaminationSetupFormValues(
            session_name="",
            examination_type=ExamSessionType.REGULAR.value,
            academic_year_label=default_year,
            semester_label="Odd",
            examination_start_at="",
            examination_end_at="",
            registration_end_at="",
            result_target_at="",
        )
        page_subtitle = "Create Examination"
        toggles = await _toggle_rules_for_session(tenant_id, None, attendance_hint=attendance_hint)
        continue_href = "/college-admin/examinations/exam-configuration"

    return ExaminationConfigurationPageRead(
        page_title="Examination Configuration",
        page_subtitle=page_subtitle,
        back_href="/college-admin/examinations/examination-session-management",
        save_draft_label="Save draft",
        continue_label="Continue",
        continue_href=continue_href,
        setup_section_title="Examination setup",
        rules_section_title="Rules",
        form=form,
        field_meta=_field_meta(),
        type_options=type_options,
        academic_year_options=year_options,
        semester_options=_SEMESTER_OPTIONS,
        toggle_rules=toggles,
        is_new=is_new,
        session_id=session.session_id if session else None,
        footer_disclaimer="Live institutional data · Examination setup · All times IST",
        footer_snapshot_label="Sample snapshot",
        generated_at=now,
    )


async def _upsert_registration_rules(
    tenant_id: PydanticObjectId,
    exam_session_id: PydanticObjectId,
    toggles: dict[str, bool],
) -> None:
    doc = await ExamSessionRegistrationRules.find_one(
        Eq(ExamSessionRegistrationRules.tenant_id, tenant_id),
        Eq(ExamSessionRegistrationRules.exam_session_id, exam_session_id),
    )
    payload = {
        "block_unpaid_students": bool(toggles.get("block_unpaid_students", True)),
        "block_below_attendance": bool(toggles.get("block_below_attendance", True)),
        "allow_late_registration": bool(toggles.get("allow_late_registration", False)),
        "updated_at": utcnow(),
    }
    if doc:
        doc.block_unpaid_students = payload["block_unpaid_students"]
        doc.block_below_attendance = payload["block_below_attendance"]
        doc.allow_late_registration = payload["allow_late_registration"]
        doc.updated_at = payload["updated_at"]
        await doc.save()
    else:
        await ExamSessionRegistrationRules(
            tenant_id=tenant_id,
            exam_session_id=exam_session_id,
            **payload,
        ).insert()


async def save_examination_configuration_page(
    scope: AccessScope,
    payload: ExaminationConfigurationSave,
) -> ExaminationConfigurationPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_CONFIG)
    tenant_id = require_college_tenant_scope(scope)
    user = await User.get(scope.user_id)
    if user is None:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)

    form = payload.form
    if not form.session_name.strip():
        raise AppError(code="VALIDATION", message="Session name is required", status_code=422)

    try:
        exam_type = ExamSessionType(form.examination_type)
    except ValueError as exc:
        raise AppError(code="VALIDATION", message="Invalid examination type", status_code=422) from exc

    exam_start = _parse_form_date(form.examination_start_at)
    exam_end = _parse_form_date(form.examination_end_at)
    registration_end = _parse_form_date(form.registration_end_at)
    result_target = _parse_form_date(form.result_target_at) if form.result_target_at.strip() else None
    registration_start = min(utcnow(), registration_end - timedelta(days=1))

    session: ExamSession | None = None
    if payload.session_id:
        session = await ExamSession.find_one(
            Eq(ExamSession.tenant_id, tenant_id),
            Eq(ExamSession.session_id, payload.session_id),
        )
        if session is None:
            raise AppError(code="NOT_FOUND", message="Examination session not found", status_code=404)

    scope_input = ExamSessionAcademicScopeInput()

    if session is None:
        session_code = f"EX-{uuid4().hex[:8].upper()}"
        create_payload = ExamSessionCreate(
            session_code=session_code,
            name=form.session_name.strip(),
            examination_type=exam_type,
            academic_year_label=form.academic_year_label.strip(),
            semester_label=form.semester_label.strip(),
            registration_start_at=registration_start,
            registration_end_at=registration_end,
            examination_start_at=exam_start,
            examination_end_at=exam_end,
            result_processing_deadline_at=result_target,
            academic_scope=scope_input,
        )
        created = await create_exam_session(scope, user, create_payload)
        session = await ExamSession.find_one(
            Eq(ExamSession.tenant_id, tenant_id),
            Eq(ExamSession.session_id, created.session_id),
        )
        if session is None:
            raise AppError(code="SERVER", message="Failed to create session", status_code=500)
    else:
        update_payload = ExamSessionUpdate(
            name=form.session_name.strip(),
            registration_start_at=registration_start,
            registration_end_at=registration_end,
            examination_start_at=exam_start,
            examination_end_at=exam_end,
            result_processing_deadline_at=result_target,
            academic_scope=scope_input,
        )
        await update_exam_session(scope, user, session.id, update_payload)
        session = await ExamSession.get(session.id)

    assert session is not None
    await _upsert_registration_rules(tenant_id, session.id, payload.toggle_rules)

    if payload.advance_workflow and session.status == ExamSessionStatus.DRAFT:
        await transition_exam_session(
            scope,
            user,
            session.id,
            ExamSessionTransitionRequest(action=ExamSessionLifecycleAction.SCHEDULE),
        )

    return await get_examination_configuration_page(scope, session_id=session.session_id)