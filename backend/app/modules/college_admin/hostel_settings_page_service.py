"""Hostel settings page (CA 13.15)."""

from __future__ import annotations

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.college_admin.academic_config_models import AcademicRegulation
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    HostelSettingsFormValues,
    HostelSettingsPageRead,
    HostelSettingsSave,
    HostelSettingsToggleRule,
    InstitutionFieldMeta,
    InstitutionFieldOption,
)
from app.modules.hostel.mess_models import HostelMessPlan

_SCOPE_KEY = "hostel_administration_settings"

_FIELD_META = [
    InstitutionFieldMeta(key="gate_closing_boys", label="Gate closing – boys", field_type="time", required=False),
    InstitutionFieldMeta(key="gate_closing_girls", label="Gate closing – girls", field_type="time", required=False),
    InstitutionFieldMeta(key="visiting_hours", label="Visiting hours", field_type="text", required=False),
    InstitutionFieldMeta(key="security_deposit", label="Security deposit", field_type="text", required=False),
    InstitutionFieldMeta(
        key="outpass_approver",
        label="Outpass approver",
        field_type="select",
        required=False,
    ),
    InstitutionFieldMeta(key="mess_plans", label="Mess plans", field_type="select", required=False),
]

_OUTPASS_APPROVER_OPTIONS = [
    InstitutionFieldOption(value="warden_to_admin", label="Warden → Admin"),
    InstitutionFieldOption(value="warden_only", label="Warden only"),
    InstitutionFieldOption(value="admin_only", label="Admin only"),
]


async def _mess_plan_options(tenant_id) -> list[InstitutionFieldOption]:
    plans = await HostelMessPlan.find(Eq(HostelMessPlan.tenant_id, tenant_id)).sort("title").to_list()
    options: list[InstitutionFieldOption] = []
    for plan in plans:
        label = (plan.title or plan.plan_code or "").strip()
        value = (plan.plan_code or label).strip()
        if not value:
            continue
        options.append(InstitutionFieldOption(value=value, label=label or value))
    if not options:
        options.append(InstitutionFieldOption(value="", label="No mess plans configured"))
    return options


async def _load_rules(tenant_id) -> dict[str, object]:
    doc = await AcademicRegulation.find_one(
        Eq(AcademicRegulation.tenant_id, tenant_id),
        Eq(AcademicRegulation.scope_key, _SCOPE_KEY),
    )
    if not doc or not doc.rules:
        return {}
    return dict(doc.rules)


def _form_values(rules: dict[str, object]) -> HostelSettingsFormValues:
    return HostelSettingsFormValues(
        gate_closing_boys=str(rules.get("gate_closing_boys") or ""),
        gate_closing_girls=str(rules.get("gate_closing_girls") or ""),
        visiting_hours=str(rules.get("visiting_hours") or ""),
        security_deposit=str(rules.get("security_deposit") or ""),
        outpass_approver=str(rules.get("outpass_approver") or ""),
        mess_plans=str(rules.get("mess_plans") or ""),
        notify_guardian_on_outpass=bool(rules.get("notify_guardian_on_outpass", False)),
        block_check_in_unpaid_fees=bool(rules.get("block_check_in_unpaid_fees", False)),
        allow_visitors_after_hours=bool(rules.get("allow_visitors_after_hours", False)),
    )


def _toggle_rules(form: HostelSettingsFormValues) -> list[HostelSettingsToggleRule]:
    return [
        HostelSettingsToggleRule(
            key="notify_guardian_on_outpass",
            label="Notify guardian on outpass",
            enabled=form.notify_guardian_on_outpass,
        ),
        HostelSettingsToggleRule(
            key="block_check_in_unpaid_fees",
            label="Block check-in with unpaid fees",
            enabled=form.block_check_in_unpaid_fees,
        ),
        HostelSettingsToggleRule(
            key="allow_visitors_after_hours",
            label="Allow visitors after hours",
            enabled=form.allow_visitors_after_hours,
        ),
    ]


async def get_hostel_settings_page(scope: AccessScope) -> HostelSettingsPageRead:
    authorize(scope, Permission.HOSTEL_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    rules = await _load_rules(tenant_id)
    mess_options = await _mess_plan_options(tenant_id)
    form = _form_values(rules)

    field_options: dict[str, list[InstitutionFieldOption]] = {
        "outpass_approver": _OUTPASS_APPROVER_OPTIONS,
        "mess_plans": mess_options,
    }

    return HostelSettingsPageRead(
        page_title="Hostel Settings",
        page_subtitle="Rules and timings",
        cancel_label="Cancel",
        save_label="Save",
        hostel_rules_section_title="Hostel rules",
        controls_section_title="Controls",
        field_meta=_FIELD_META,
        field_options=field_options,
        form=form,
        toggle_rules=_toggle_rules(form),
        generated_at=now,
    )


async def save_hostel_settings_page(scope: AccessScope, payload: HostelSettingsSave) -> HostelSettingsPageRead:
    authorize(scope, Permission.HOSTEL_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    form = payload.form
    rules = {**form.model_dump()}
    doc = await AcademicRegulation.find_one(
        Eq(AcademicRegulation.tenant_id, tenant_id),
        Eq(AcademicRegulation.scope_key, _SCOPE_KEY),
    )
    if doc is None:
        doc = AcademicRegulation(
            tenant_id=tenant_id,
            scope_key=_SCOPE_KEY,
            rules=rules,
            updated_by=scope.user_id,
        )
        await doc.insert()
    else:
        doc.rules = rules
        doc.updated_by = scope.user_id
        doc.updated_at = utcnow()
        await doc.save()

    return await get_hostel_settings_page(scope)