"""Attendance configuration and rules & policies pages (CA 08.10 / 08.11)."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.attendance.models import AttendancePolicyRules
from app.modules.college_admin.attendance_admin_models import (
    AttendanceInstitutionalPolicyRow,
    AttendancePolicyAudience,
    InstitutionAttendanceMarkingConfig,
    InstitutionAttendancePolicy,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AttendanceConfigurationFieldMeta,
    AttendanceConfigurationPageRead,
    AttendanceConfigurationSave,
    AttendanceConfigurationToggleRule,
    AttendanceRulesPoliciesPageRead,
    AttendanceRulesPolicyTableRow,
    InstitutionFieldOption,
)

_IST = ZoneInfo("Asia/Kolkata")
_POLICIES_PAGE_SIZE = 4

_MARKING_WINDOW_OPTIONS = [
    InstitutionFieldOption(value="same_day_18", label="Same day until 18:00"),
    InstitutionFieldOption(value="same_day_20", label="Same day until 20:00"),
    InstitutionFieldOption(value="next_day_10", label="Next day until 10:00"),
    InstitutionFieldOption(value="next_working_day_12", label="Next working day until 12:00"),
]

_CORRECTION_WINDOW_OPTIONS = [
    InstitutionFieldOption(value="2_working_days", label="2 working days"),
    InstitutionFieldOption(value="3_working_days", label="3 working days"),
    InstitutionFieldOption(value="5_working_days", label="5 working days"),
    InstitutionFieldOption(value="7_calendar_days", label="7 calendar days"),
]

_LATE_MARK_OPTIONS = [
    InstitutionFieldOption(value="10_minutes", label="10 minutes"),
    InstitutionFieldOption(value="15_minutes", label="15 minutes"),
    InstitutionFieldOption(value="20_minutes", label="20 minutes"),
    InstitutionFieldOption(value="30_minutes", label="30 minutes"),
]

_SESSION_LENGTH_OPTIONS = [
    InstitutionFieldOption(value="45_minutes", label="45 minutes"),
    InstitutionFieldOption(value="60_minutes", label="60 minutes"),
    InstitutionFieldOption(value="75_minutes", label="75 minutes"),
    InstitutionFieldOption(value="90_minutes", label="90 minutes"),
]

_VALID_MARKING = {o.value for o in _MARKING_WINDOW_OPTIONS}
_VALID_CORRECTION = {o.value for o in _CORRECTION_WINDOW_OPTIONS}
_VALID_LATE = {o.value for o in _LATE_MARK_OPTIONS}
_VALID_SESSION = {o.value for o in _SESSION_LENGTH_OPTIONS}


def _fmt_snapshot(now: datetime) -> str:
    return now.astimezone(_IST).strftime("Sample snapshot · %d %b %Y, %H:%M IST")


def _fmt_effective(day: date) -> str:
    return datetime(day.year, day.month, day.day, tzinfo=_IST).strftime("%d %b %Y")


def _deadline_hours_for_correction(key: str) -> int:
    if key == "2_working_days":
        return 48
    if key == "5_working_days":
        return 120
    if key == "7_calendar_days":
        return 168
    return 72


def _deadline_hours_for_marking(key: str) -> int:
    if key == "same_day_20":
        return 20
    if key == "next_day_10":
        return 34
    if key == "next_working_day_12":
        return 36
    return 18


async def _get_or_create_marking_config(tenant_id: PydanticObjectId, user_id: PydanticObjectId | None) -> InstitutionAttendanceMarkingConfig:
    row = await InstitutionAttendanceMarkingConfig.find_one(Eq(InstitutionAttendanceMarkingConfig.tenant_id, tenant_id))
    if row:
        return row
    row = InstitutionAttendanceMarkingConfig(tenant_id=tenant_id, updated_by=user_id)
    await row.insert()
    return row


async def _sync_submission_deadline(tenant_id: PydanticObjectId, marking_key: str) -> None:
    hours = _deadline_hours_for_marking(marking_key)
    policy = await InstitutionAttendancePolicy.find_one(
        Eq(InstitutionAttendancePolicy.tenant_id, tenant_id),
        Eq(InstitutionAttendancePolicy.audience, AttendancePolicyAudience.STUDENT),
        Eq(InstitutionAttendancePolicy.is_active, True),
    )
    if policy:
        policy.submission_deadline_hours = hours
        policy.updated_at = utcnow()
        await policy.save()


async def _ensure_policy_catalog(tenant_id: PydanticObjectId) -> list[AttendanceInstitutionalPolicyRow]:
    existing = await AttendanceInstitutionalPolicyRow.find(
        Eq(AttendanceInstitutionalPolicyRow.tenant_id, tenant_id),
    ).sort("sort_order").to_list()
    if existing:
        return existing

    student_policy = await InstitutionAttendancePolicy.find_one(
        Eq(InstitutionAttendancePolicy.tenant_id, tenant_id),
        Eq(InstitutionAttendancePolicy.audience, AttendancePolicyAudience.STUDENT),
        Eq(InstitutionAttendancePolicy.is_active, True),
    )
    min_pct = student_policy.rules.min_percentage_required if student_policy else AttendancePolicyRules().min_percentage_required
    effective = date(2026, 7, 1)
    seed = [
        ("minimum_attendance", "Minimum attendance", f"{min_pct:g}%", "All programmes", 0),
        ("condonation", "Condonation", "Up to 10%", "Medical cases", 1),
        ("shortage_notice", "Shortage notice", "At 78% and 75%", "All students", 2),
        ("exam_eligibility", "Exam eligibility", f"{min_pct:g}% overall", "Semester exams", 3),
        ("faculty_submission", "Faculty submission", "Per marking window", "All teaching faculty", 4),
        ("correction_window", "Correction window", "Per institution config", "Correction requests", 5),
    ]
    rows: list[AttendanceInstitutionalPolicyRow] = []
    for key, title, value, applies, order in seed:
        doc = AttendanceInstitutionalPolicyRow(
            tenant_id=tenant_id,
            policy_key=key,
            title=title,
            value_label=value,
            applies_to_label=applies,
            effective_from=effective,
            is_active=True,
            sort_order=order,
        )
        await doc.insert()
        rows.append(doc)
    return rows


def _field_meta() -> list[AttendanceConfigurationFieldMeta]:
    return [
        AttendanceConfigurationFieldMeta(key="marking_window_key", label="Marking window"),
        AttendanceConfigurationFieldMeta(key="correction_window_key", label="Correction window"),
        AttendanceConfigurationFieldMeta(key="late_mark_after_key", label="Late mark after"),
        AttendanceConfigurationFieldMeta(key="session_length_key", label="Session length"),
    ]


def _toggle_rules(cfg: InstitutionAttendanceMarkingConfig) -> list[AttendanceConfigurationToggleRule]:
    return [
        AttendanceConfigurationToggleRule(
            key="allow_substitute_faculty",
            label="Allow substitute faculty",
            description="Marked under original class",
            enabled=cfg.allow_substitute_faculty,
        ),
        AttendanceConfigurationToggleRule(
            key="lock_after_approval",
            label="Lock after approval",
            description="No edits without request",
            enabled=cfg.lock_after_approval,
        ),
        AttendanceConfigurationToggleRule(
            key="biometric_sync",
            label="Biometric sync",
            description="Where devices are installed",
            enabled=cfg.biometric_sync,
        ),
    ]


async def get_attendance_configuration_page(scope: AccessScope) -> AttendanceConfigurationPageRead:
    authorize(scope, Permission.ATTENDANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    cfg = await _get_or_create_marking_config(tenant_id, scope.user_id)
    await _ensure_policy_catalog(tenant_id)

    return AttendanceConfigurationPageRead(
        page_title="Attendance Configuration",
        page_subtitle="Marking windows and sessions",
        cancel_label="Cancel",
        save_label="Save",
        rules_policies_href="/college-admin/attendance/attendance-rules-policies",
        rules_policies_link_label="Rules & policies",
        marking_section_title="Marking rules",
        behaviour_section_title="Behaviour",
        marking_window_key=cfg.marking_window_key,
        correction_window_key=cfg.correction_window_key,
        late_mark_after_key=cfg.late_mark_after_key,
        session_length_key=cfg.session_length_key,
        marking_window_options=_MARKING_WINDOW_OPTIONS,
        correction_window_options=_CORRECTION_WINDOW_OPTIONS,
        late_mark_after_options=_LATE_MARK_OPTIONS,
        session_length_options=_SESSION_LENGTH_OPTIONS,
        field_meta=_field_meta(),
        toggle_rules=_toggle_rules(cfg),
        footer_disclaimer="Illustrative data only · No live student, faculty or finance records · All times IST",
        footer_snapshot_label=_fmt_snapshot(now),
        generated_at=now,
    )


async def save_attendance_configuration(scope: AccessScope, payload: AttendanceConfigurationSave) -> AttendanceConfigurationPageRead:
    authorize(scope, Permission.ATTENDANCE_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    if payload.marking_window_key not in _VALID_MARKING:
        raise AppError(code="VALIDATION_ERROR", message="Invalid marking window", status_code=422)
    if payload.correction_window_key not in _VALID_CORRECTION:
        raise AppError(code="VALIDATION_ERROR", message="Invalid correction window", status_code=422)
    if payload.late_mark_after_key not in _VALID_LATE:
        raise AppError(code="VALIDATION_ERROR", message="Invalid late mark threshold", status_code=422)
    if payload.session_length_key not in _VALID_SESSION:
        raise AppError(code="VALIDATION_ERROR", message="Invalid session length", status_code=422)

    cfg = await _get_or_create_marking_config(tenant_id, scope.user_id)
    cfg.marking_window_key = payload.marking_window_key
    cfg.correction_window_key = payload.correction_window_key
    cfg.late_mark_after_key = payload.late_mark_after_key
    cfg.session_length_key = payload.session_length_key
    cfg.allow_substitute_faculty = bool(payload.toggle_rules.get("allow_substitute_faculty", cfg.allow_substitute_faculty))
    cfg.lock_after_approval = bool(payload.toggle_rules.get("lock_after_approval", cfg.lock_after_approval))
    cfg.biometric_sync = bool(payload.toggle_rules.get("biometric_sync", cfg.biometric_sync))
    cfg.updated_by = scope.user_id
    cfg.updated_at = utcnow()
    await cfg.save()

    await _sync_submission_deadline(tenant_id, cfg.marking_window_key)

    correction_row = await AttendanceInstitutionalPolicyRow.find_one(
        Eq(AttendanceInstitutionalPolicyRow.tenant_id, tenant_id),
        Eq(AttendanceInstitutionalPolicyRow.policy_key, "correction_window"),
    )
    if correction_row:
        label = next((o.label for o in _CORRECTION_WINDOW_OPTIONS if o.value == cfg.correction_window_key), cfg.correction_window_key)
        correction_row.value_label = label
        correction_row.updated_at = utcnow()
        await correction_row.save()

    faculty_row = await AttendanceInstitutionalPolicyRow.find_one(
        Eq(AttendanceInstitutionalPolicyRow.tenant_id, tenant_id),
        Eq(AttendanceInstitutionalPolicyRow.policy_key, "faculty_submission"),
    )
    if faculty_row:
        label = next((o.label for o in _MARKING_WINDOW_OPTIONS if o.value == cfg.marking_window_key), cfg.marking_window_key)
        faculty_row.value_label = label
        faculty_row.updated_at = utcnow()
        await faculty_row.save()

    from app.modules.audit.service import record_audit

    await record_audit(
        actor_id=scope.user_id,
        action="college.attendance.configuration_saved",
        resource_type="institution_attendance_marking_config",
        resource_id=str(cfg.id),
        tenant_id=tenant_id,
    )
    return await get_attendance_configuration_page(scope)


async def get_attendance_rules_policies_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _POLICIES_PAGE_SIZE,
) -> AttendanceRulesPoliciesPageRead:
    authorize(scope, Permission.ATTENDANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    all_rows = await _ensure_policy_catalog(tenant_id)

    student_policy = await InstitutionAttendancePolicy.find_one(
        Eq(InstitutionAttendancePolicy.tenant_id, tenant_id),
        Eq(InstitutionAttendancePolicy.audience, AttendancePolicyAudience.STUDENT),
        Eq(InstitutionAttendancePolicy.is_active, True),
    )
    if student_policy:
        min_pct = student_policy.rules.min_percentage_required
        for row in all_rows:
            if row.policy_key == "minimum_attendance":
                row.value_label = f"{min_pct:g}%"
            if row.policy_key == "exam_eligibility":
                row.value_label = f"{min_pct:g}% overall"

    page = max(1, page)
    page_size = max(1, min(page_size, 20))
    total = len(all_rows)
    start = (page - 1) * page_size
    visible = all_rows[start : start + page_size]

    table_rows: list[AttendanceRulesPolicyTableRow] = []
    for row in visible:
        status_label = "Active" if row.is_active else "Inactive"
        tone = "success" if row.is_active else "muted"
        table_rows.append(
            AttendanceRulesPolicyTableRow(
                row_key=row.policy_key,
                policy_title=row.title,
                value_label=row.value_label,
                applies_to_label=row.applies_to_label,
                effective_label=_fmt_effective(row.effective_from),
                status_label=status_label,
                status_tone=tone,
            ),
        )

    return AttendanceRulesPoliciesPageRead(
        page_title="Attendance Rules & Policies",
        page_subtitle="Minimum attendance and condonation",
        configuration_href="/college-admin/attendance/attendance-configuration",
        back_label="Back to configuration",
        cancel_label="Cancel",
        save_label="Save",
        policies_section_title="Policies",
        policies_table_headers=["Policy", "Value", "Applies to", "Effective", "Status"],
        policy_rows=table_rows,
        policies_table_footer_label=f"{len(table_rows)} of {total} policies",
        footer_disclaimer="Illustrative data only · No live student, faculty or finance records · All times IST",
        footer_snapshot_label=_fmt_snapshot(now),
        generated_at=now,
    )