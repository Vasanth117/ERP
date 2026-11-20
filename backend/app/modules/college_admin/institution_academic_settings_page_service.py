"""Academic institution settings page (CA — academic settings)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.audit.service import record_audit
from app.modules.college_admin.academic_config_models import AcademicRegulation, ConfigPublicationStatus
from app.modules.college_admin.identity_models import DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AcademicInstitutionAppliesRow,
    AcademicInstitutionFieldGroup,
    AcademicInstitutionFormValues,
    AcademicInstitutionSettingsPageRead,
    AcademicInstitutionSettingsSave,
    AcademicInstitutionToggleRule,
    InstitutionFieldMeta,
    InstitutionFieldOption,
)

_SCOPE_KEY = "institution_academic_defaults"

_DEFAULT_VALUES: dict[str, Any] = {
    "academic_pattern": "semester_2",
    "credit_system": "cbcs",
    "working_days_per_semester": "90",
    "teaching_week": "mon_saturday",
    "periods_per_day": "8",
    "period_duration_minutes": "50",
    "minimum_attendance_for_exams": "75%",
    "condonation_band": "65% – 74%",
    "attendance_calculation": "subject_wise",
    "medical_leave_counted_present": "up_to_10_days",
    "internal_external_weightage": "40 : 60",
    "pass_mark_external": "45 / 100",
    "pass_mark_overall": "50 / 100",
    "grading_scheme": "10_point_relative",
    "allow_re_registration_failed_courses": True,
    "enable_grace_marks": True,
    "auto_detain_below_attendance": False,
    "lock_marks_after_result_approval": True,
}

_FIELD_OPTIONS: dict[str, list[InstitutionFieldOption]] = {
    "academic_pattern": [
        InstitutionFieldOption(value="semester_2", label="Semester (2 per year)"),
        InstitutionFieldOption(value="semester_1", label="Annual (1 per year)"),
        InstitutionFieldOption(value="trimester", label="Trimester (3 per year)"),
    ],
    "credit_system": [
        InstitutionFieldOption(value="cbcs", label="Choice-based credit system (CBCS)"),
        InstitutionFieldOption(value="conventional", label="Conventional credit hours"),
    ],
    "teaching_week": [
        InstitutionFieldOption(value="mon_saturday", label="Monday – Saturday"),
        InstitutionFieldOption(value="mon_friday", label="Monday – Friday"),
    ],
    "attendance_calculation": [
        InstitutionFieldOption(value="subject_wise", label="Subject-wise"),
        InstitutionFieldOption(value="programme_wise", label="Programme-wise"),
        InstitutionFieldOption(value="daily", label="Daily consolidated"),
    ],
    "medical_leave_counted_present": [
        InstitutionFieldOption(value="up_to_10_days", label="Up to 10 days"),
        InstitutionFieldOption(value="up_to_15_days", label="Up to 15 days"),
        InstitutionFieldOption(value="none", label="Not counted as present"),
    ],
    "grading_scheme": [
        InstitutionFieldOption(value="10_point_relative", label="10-point relative grading"),
        InstitutionFieldOption(value="10_point_absolute", label="10-point absolute grading"),
        InstitutionFieldOption(value="letter_grade", label="Letter grade (A–F)"),
    ],
}

_FIELD_META: list[InstitutionFieldMeta] = [
    InstitutionFieldMeta(key="academic_pattern", label="Academic pattern", required=True, field_type="select"),
    InstitutionFieldMeta(key="credit_system", label="Credit system", required=True, field_type="select"),
    InstitutionFieldMeta(key="working_days_per_semester", label="Working days per semester", required=True),
    InstitutionFieldMeta(key="teaching_week", label="Teaching week", required=False, field_type="select"),
    InstitutionFieldMeta(key="periods_per_day", label="Periods per day", required=True),
    InstitutionFieldMeta(key="period_duration_minutes", label="Period duration (minutes)", required=True),
    InstitutionFieldMeta(key="minimum_attendance_for_exams", label="Minimum attendance for exams", required=True),
    InstitutionFieldMeta(key="condonation_band", label="Condonation band", required=False),
    InstitutionFieldMeta(key="attendance_calculation", label="Attendance calculation", required=False, field_type="select"),
    InstitutionFieldMeta(
        key="medical_leave_counted_present",
        label="Medical leave counted as present",
        required=False,
        field_type="select",
    ),
    InstitutionFieldMeta(key="internal_external_weightage", label="Internal : external weightage", required=True),
    InstitutionFieldMeta(key="pass_mark_external", label="Pass mark – external", required=True),
    InstitutionFieldMeta(key="pass_mark_overall", label="Pass mark – overall", required=True),
    InstitutionFieldMeta(key="grading_scheme", label="Grading scheme", required=True, field_type="select"),
]

_TOGGLE_RULES: list[tuple[str, str, str]] = [
    (
        "allow_re_registration_failed_courses",
        "Allow re-registration of failed courses",
        "Students can register again in the next semester",
    ),
    ("enable_grace_marks", "Enable grace marks", "Up to 5 marks for borderline cases"),
    (
        "auto_detain_below_attendance",
        "Auto-detain below 65% attendance",
        "Requires Principal override to release",
    ),
    (
        "lock_marks_after_result_approval",
        "Lock marks after result approval",
        "Prevents edits after publication",
    ),
]

_GROUPS = [
    AcademicInstitutionFieldGroup(key="academic_structure", title="Academic structure", field_keys=[
        "academic_pattern",
        "credit_system",
        "working_days_per_semester",
        "teaching_week",
        "periods_per_day",
        "period_duration_minutes",
    ]),
    AcademicInstitutionFieldGroup(key="attendance_eligibility", title="Attendance & eligibility", field_keys=[
        "minimum_attendance_for_exams",
        "condonation_band",
        "attendance_calculation",
        "medical_leave_counted_present",
    ]),
    AcademicInstitutionFieldGroup(key="assessment_rules", title="Assessment rules", field_keys=[
        "internal_external_weightage",
        "pass_mark_external",
        "pass_mark_overall",
        "grading_scheme",
    ]),
]


def _coerce_form(rules: dict[str, Any]) -> AcademicInstitutionFormValues:
    merged = {**_DEFAULT_VALUES, **rules}
    return AcademicInstitutionFormValues(
        academic_pattern=str(merged["academic_pattern"]),
        credit_system=str(merged["credit_system"]),
        working_days_per_semester=str(merged["working_days_per_semester"]),
        teaching_week=str(merged["teaching_week"]),
        periods_per_day=str(merged["periods_per_day"]),
        period_duration_minutes=str(merged["period_duration_minutes"]),
        minimum_attendance_for_exams=str(merged["minimum_attendance_for_exams"]),
        condonation_band=str(merged.get("condonation_band") or ""),
        attendance_calculation=str(merged["attendance_calculation"]),
        medical_leave_counted_present=str(merged["medical_leave_counted_present"]),
        internal_external_weightage=str(merged["internal_external_weightage"]),
        pass_mark_external=str(merged["pass_mark_external"]),
        pass_mark_overall=str(merged["pass_mark_overall"]),
        grading_scheme=str(merged["grading_scheme"]),
        allow_re_registration_failed_courses=bool(merged["allow_re_registration_failed_courses"]),
        enable_grace_marks=bool(merged["enable_grace_marks"]),
        auto_detain_below_attendance=bool(merged["auto_detain_below_attendance"]),
        lock_marks_after_result_approval=bool(merged["lock_marks_after_result_approval"]),
    )


async def _load_rules(tenant_id: PydanticObjectId) -> dict[str, Any]:
    doc = await AcademicRegulation.find_one(
        Eq(AcademicRegulation.tenant_id, tenant_id),
        Eq(AcademicRegulation.scope_key, _SCOPE_KEY),
    )
    if doc is None:
        return deepcopy(_DEFAULT_VALUES)
    return {**_DEFAULT_VALUES, **doc.rules}


async def _applies_to(tenant_id: PydanticObjectId) -> list[AcademicInstitutionAppliesRow]:
    dept_count = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).count()
    regulations = await AcademicRegulation.find(Eq(AcademicRegulation.tenant_id, tenant_id)).to_list()
    override_count = sum(
        1
        for row in regulations
        if row.scope_key != _SCOPE_KEY and row.scope_key.startswith("department:")
    )
    dept_label = f"{dept_count} department{'s' if dept_count != 1 else ''}"
    return [
        AcademicInstitutionAppliesRow(
            key="departments",
            title=dept_label,
            description="All programmes inherit these rules",
            href="/college-admin/organization/department-management-dashboard",
            icon_slug="network",
            badge_label=None,
            badge_tone=None,
        ),
        AcademicInstitutionAppliesRow(
            key="department_overrides",
            title="Department overrides",
            description=(
                f"{override_count} department{'s have' if override_count != 1 else ' has'} overrides"
                if override_count
                else "No department-specific overrides"
            ),
            href="/college-admin/academics/academic-configuration-dashboard",
            icon_slug="sliders-horizontal",
            badge_label="Review" if override_count else None,
            badge_tone="warning" if override_count else None,
        ),
    ]


async def get_academic_institution_settings_page(scope: AccessScope) -> AcademicInstitutionSettingsPageRead:
    authorize(scope, Permission.INSTITUTION_SETTINGS_READ)
    tenant_id = require_college_tenant_scope(scope)
    rules = await _load_rules(tenant_id)
    form = _coerce_form(rules)
    toggles = [
        AcademicInstitutionToggleRule(
            key=key,
            label=label,
            description=description,
            enabled=bool(getattr(form, key)),
        )
        for key, label, description in _TOGGLE_RULES
    ]
    return AcademicInstitutionSettingsPageRead(
        page_title="Academic Institution Settings",
        page_subtitle="College-wide academic rules applied to every department and programme",
        reset_label="Reset to defaults",
        save_label="Save settings",
        footer_note="Changes are saved to the audit log with your name and time.",
        form=form,
        field_meta=_FIELD_META,
        field_options=_FIELD_OPTIONS,
        field_groups=_GROUPS,
        toggle_rules=toggles,
        applies_to=await _applies_to(tenant_id),
        generated_at=utcnow(),
    )


async def _persist_rules(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    rules: dict[str, Any],
) -> None:
    doc = await AcademicRegulation.find_one(
        Eq(AcademicRegulation.tenant_id, tenant_id),
        Eq(AcademicRegulation.scope_key, _SCOPE_KEY),
    )
    if doc is None:
        doc = AcademicRegulation(
            tenant_id=tenant_id,
            scope_key=_SCOPE_KEY,
            rules=rules,
            status=ConfigPublicationStatus.PUBLISHED,
            updated_by=scope.user_id,
        )
        await doc.insert()
        return
    doc.rules = rules
    doc.status = ConfigPublicationStatus.PUBLISHED
    doc.version += 1
    doc.updated_at = utcnow()
    doc.updated_by = scope.user_id
    await doc.save()


async def save_academic_institution_settings_page(
    scope: AccessScope,
    payload: AcademicInstitutionSettingsSave,
) -> AcademicInstitutionSettingsPageRead:
    authorize(scope, Permission.INSTITUTION_SETTINGS_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    form = payload.form
    rules = form.model_dump(mode="json")
    await _persist_rules(scope, tenant_id, rules)
    await record_audit(
        actor_id=scope.user_id,
        action="institution.academic_settings.updated",
        resource_type="academic_regulation",
        resource_id=_SCOPE_KEY,
        tenant_id=tenant_id,
    )
    return await get_academic_institution_settings_page(scope)


async def reset_academic_institution_settings_page(scope: AccessScope) -> AcademicInstitutionSettingsPageRead:
    authorize(scope, Permission.INSTITUTION_SETTINGS_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    defaults = deepcopy(_DEFAULT_VALUES)
    await _persist_rules(scope, tenant_id, defaults)
    await record_audit(
        actor_id=scope.user_id,
        action="institution.academic_settings.reset",
        resource_type="academic_regulation",
        resource_id=_SCOPE_KEY,
        tenant_id=tenant_id,
    )
    return await get_academic_institution_settings_page(scope)