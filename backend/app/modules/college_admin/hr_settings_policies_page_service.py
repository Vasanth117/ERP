"""HR settings & policies page (CA 11.14)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.college_admin.academic_config_models import AcademicRegulation, ConfigPublicationStatus
from app.modules.college_admin.hr_admin_models import EmployeeLeavePolicy, PayrollConfiguration
from app.modules.college_admin.hr_admin_schemas import LeavePolicyUpsert
from app.modules.college_admin.hr_admin_service import upsert_leave_policy
from app.modules.college_admin.hr_reports_settings_shared import HR_REPORTS_SETTINGS_SUB_NAV
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    HrSettingsPoliciesFormValues,
    HrSettingsPoliciesPageRead,
    HrSettingsPoliciesSave,
    HrSettingsPoliciesToggleRule,
    InstitutionFieldMeta,
    InstitutionFieldOption,
)
from app.modules.audit.service import record_audit

_IST = ZoneInfo("Asia/Kolkata")
_SCOPE_KEY = "hr_administration_settings"
_DEFAULT_CONFIG_ID = "default"

_DEFAULTS: dict[str, Any] = {
    "working_week": "mon_sat",
    "earned_leave_per_year": "30",
    "casual_leave_per_year": "12",
    "leave_approver": "hod_hr",
    "probation_period_months": "12",
    "payroll_cutoff_day": "25",
    "carry_forward_earned_leave": True,
    "carry_forward_max_days": "60",
    "auto_lock_attendance_before_payroll": True,
    "self_service_salary_slips": True,
}

_FIELD_META = [
    InstitutionFieldMeta(key="working_week", label="Working week", field_type="select", required=True),
    InstitutionFieldMeta(key="earned_leave_per_year", label="Earned leave per year", field_type="text", required=True),
    InstitutionFieldMeta(key="leave_approver", label="Leave approver", field_type="select", required=True),
    InstitutionFieldMeta(key="casual_leave_per_year", label="Casual leave per year", field_type="text", required=True),
    InstitutionFieldMeta(key="probation_period_months", label="Probation period", field_type="select", required=True),
    InstitutionFieldMeta(key="payroll_cutoff_day", label="Payroll cut-off day", field_type="select", required=True),
]

_FIELD_OPTIONS: dict[str, list[InstitutionFieldOption]] = {
    "working_week": [
        InstitutionFieldOption(value="mon_sat", label="Monday – Saturday"),
        InstitutionFieldOption(value="mon_fri", label="Monday – Friday"),
        InstitutionFieldOption(value="mon_sun", label="All week"),
    ],
    "leave_approver": [
        InstitutionFieldOption(value="hod_hr", label="HOD → HR"),
        InstitutionFieldOption(value="hod_only", label="HOD only"),
        InstitutionFieldOption(value="hr_only", label="HR only"),
    ],
    "probation_period_months": [
        InstitutionFieldOption(value="6", label="6 months"),
        InstitutionFieldOption(value="12", label="12 months"),
        InstitutionFieldOption(value="18", label="18 months"),
    ],
    "payroll_cutoff_day": [InstitutionFieldOption(value=str(d), label=str(d)) for d in range(20, 29)],
}

_TOGGLE_DEFS = (
    (
        "carry_forward_earned_leave",
        "Carry forward earned leave",
        "Up to 60 days",
        "Allow unused earned leave to carry forward within configured limits.",
    ),
    (
        "auto_lock_attendance_before_payroll",
        "Auto-lock attendance before payroll",
        "",
        "Lock attendance data after the payroll cut-off.",
    ),
    (
        "self_service_salary_slips",
        "Self-service salary slips",
        "",
        "Employees may download published slips from their portal.",
    ),
)


def _fmt_snapshot(now: datetime) -> str:
    return now.astimezone(_IST).strftime("Snapshot · %d %b %Y, %H:%M IST")


def _coerce_form(rules: dict[str, Any]) -> HrSettingsPoliciesFormValues:
    return HrSettingsPoliciesFormValues(
        working_week=str(rules.get("working_week", _DEFAULTS["working_week"])),
        earned_leave_per_year=str(rules.get("earned_leave_per_year", _DEFAULTS["earned_leave_per_year"])),
        casual_leave_per_year=str(rules.get("casual_leave_per_year", _DEFAULTS["casual_leave_per_year"])),
        leave_approver=str(rules.get("leave_approver", _DEFAULTS["leave_approver"])),
        probation_period_months=str(rules.get("probation_period_months", _DEFAULTS["probation_period_months"])),
        payroll_cutoff_day=str(rules.get("payroll_cutoff_day", _DEFAULTS["payroll_cutoff_day"])),
        carry_forward_earned_leave=bool(rules.get("carry_forward_earned_leave", True)),
        auto_lock_attendance_before_payroll=bool(rules.get("auto_lock_attendance_before_payroll", True)),
        self_service_salary_slips=bool(rules.get("self_service_salary_slips", True)),
    )


async def _load_rules(tenant_id) -> dict[str, Any]:
    merged = dict(_DEFAULTS)
    doc = await AcademicRegulation.find_one(
        Eq(AcademicRegulation.tenant_id, tenant_id),
        Eq(AcademicRegulation.scope_key, _SCOPE_KEY),
    )
    if doc and doc.rules:
        merged.update(doc.rules)

    earned = await EmployeeLeavePolicy.find_one(
        Eq(EmployeeLeavePolicy.tenant_id, tenant_id),
        Eq(EmployeeLeavePolicy.leave_type, "earned"),
    )
    if earned:
        merged["earned_leave_per_year"] = str(int(earned.annual_quota_days) if earned.annual_quota_days % 1 == 0 else earned.annual_quota_days)
        merged["carry_forward_earned_leave"] = bool(earned.rules.get("carry_forward_enabled", merged["carry_forward_earned_leave"]))
        if earned.rules.get("carry_forward_max_days") is not None:
            merged["carry_forward_max_days"] = str(earned.rules["carry_forward_max_days"])

    casual = await EmployeeLeavePolicy.find_one(
        Eq(EmployeeLeavePolicy.tenant_id, tenant_id),
        Eq(EmployeeLeavePolicy.leave_type, "casual"),
    )
    if casual:
        merged["casual_leave_per_year"] = str(int(casual.annual_quota_days) if casual.annual_quota_days % 1 == 0 else casual.annual_quota_days)

    payroll = await PayrollConfiguration.find_one(
        Eq(PayrollConfiguration.tenant_id, tenant_id),
        Eq(PayrollConfiguration.config_id, _DEFAULT_CONFIG_ID),
    )
    if payroll and payroll.confidential_config:
        cutoff = payroll.confidential_config.get("payroll_cutoff_day")
        if cutoff is not None:
            merged["payroll_cutoff_day"] = str(cutoff)
        merged["auto_lock_attendance_before_payroll"] = bool(
            payroll.confidential_config.get("auto_lock_attendance_before_payroll", merged["auto_lock_attendance_before_payroll"])
        )
        merged["self_service_salary_slips"] = bool(
            payroll.confidential_config.get("self_service_salary_slips", merged["self_service_salary_slips"])
        )
    return merged


async def _persist_rules(scope: AccessScope, tenant_id, rules: dict[str, Any]) -> None:
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


async def _sync_domain_policies(scope: AccessScope, form: HrSettingsPoliciesFormValues) -> None:
    try:
        earned_days = float(form.earned_leave_per_year)
        casual_days = float(form.casual_leave_per_year)
    except ValueError as exc:
        from app.core.exceptions import AppError

        raise AppError(code="VALIDATION_ERROR", message="Leave quotas must be numeric", status_code=422) from exc

    await upsert_leave_policy(
        scope,
        LeavePolicyUpsert(
            leave_type="earned",
            annual_quota_days=earned_days,
            requires_approval=True,
            rules={
                "carry_forward_enabled": form.carry_forward_earned_leave,
                "carry_forward_max_days": int(_DEFAULTS.get("carry_forward_max_days", 60)),
                "approver_chain": form.leave_approver,
            },
        ),
    )
    await upsert_leave_policy(
        scope,
        LeavePolicyUpsert(
            leave_type="casual",
            annual_quota_days=casual_days,
            requires_approval=True,
            rules={"approver_chain": form.leave_approver},
        ),
    )

    try:
        cutoff = int(form.payroll_cutoff_day)
    except ValueError as exc:
        from app.core.exceptions import AppError

        raise AppError(code="VALIDATION_ERROR", message="Payroll cut-off day must be numeric", status_code=422) from exc

    payroll_rules = {
        "payroll_cutoff_day": cutoff,
        "auto_lock_attendance_before_payroll": form.auto_lock_attendance_before_payroll,
        "self_service_salary_slips": form.self_service_salary_slips,
        "working_week": form.working_week,
        "probation_period_months": int(form.probation_period_months),
    }
    tenant_id = require_college_tenant_scope(scope)
    payroll = await PayrollConfiguration.find_one(
        Eq(PayrollConfiguration.tenant_id, tenant_id),
        Eq(PayrollConfiguration.config_id, _DEFAULT_CONFIG_ID),
    )
    if payroll:
        payroll.confidential_config = {**payroll.confidential_config, **payroll_rules}
        payroll.version += 1
        payroll.updated_by = scope.user_id
        payroll.updated_at = utcnow()
        await payroll.save()
    else:
        await PayrollConfiguration(
            tenant_id=tenant_id,
            config_id=_DEFAULT_CONFIG_ID,
            label="College payroll",
            pay_frequency="monthly",
            confidential_config=payroll_rules,
            updated_by=scope.user_id,
        ).insert()


async def get_hr_settings_policies_page(scope: AccessScope) -> HrSettingsPoliciesPageRead:
    authorize(scope, Permission.HR_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    rules = await _load_rules(tenant_id)
    form = _coerce_form(rules)
    toggles = [
        HrSettingsPoliciesToggleRule(
            key=key,
            label=label,
            description=description,
            badge_label=badge,
            enabled=bool(getattr(form, key)),
        )
        for key, label, badge, description in _TOGGLE_DEFS
    ]
    return HrSettingsPoliciesPageRead(
        page_title="HR Settings & Policies",
        page_subtitle="Leave, attendance and payroll policies",
        cancel_label="Cancel",
        save_label="Save",
        policies_section_title="Policies",
        controls_section_title="Controls",
        sub_nav=HR_REPORTS_SETTINGS_SUB_NAV,
        form=form,
        field_meta=_FIELD_META,
        field_options=_FIELD_OPTIONS,
        toggle_rules=toggles,
        footer_disclaimer="Published policies apply to new leave and payroll cycles.",
        footer_snapshot_label=_fmt_snapshot(now),
        generated_at=now,
    )


async def save_hr_settings_policies_page(scope: AccessScope, payload: HrSettingsPoliciesSave) -> HrSettingsPoliciesPageRead:
    authorize(scope, Permission.HR_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    rules = payload.form.model_dump(mode="json")
    await _persist_rules(scope, tenant_id, rules)
    await _sync_domain_policies(scope, payload.form)
    await record_audit(
        actor_id=scope.user_id,
        action="hr.settings_policies.page_updated",
        resource_type="academic_regulation",
        resource_id=_SCOPE_KEY,
        tenant_id=tenant_id,
    )
    return await get_hr_settings_policies_page(scope)