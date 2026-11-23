"""Finance settings page (CA 10.13)."""

from __future__ import annotations

from typing import Any

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.accounts_finance.finance_settings_service import DEFAULT_FEE, DEFAULT_PAYMENT, DEFAULT_RECEIPT
from app.modules.accounts_finance.phase12_enums import FinanceSettingStatus, FinanceSettingsDomain
from app.modules.accounts_finance.phase12_models import FinancePaymentSettings, FinanceReceiptSettings, FinanceSettingsRecord
from app.modules.accounts_finance.phase3_models import PaymentGatewayConfiguration
from app.modules.college_admin.academic_config_models import AcademicRegulation, ConfigPublicationStatus
from app.modules.college_admin.finance_admin_models import FinancialPeriod
from app.modules.accounts_finance.phase12_models import FinanceApprovalWorkflow
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    FinanceSettingsFormValues,
    FinanceSettingsPageRead,
    FinanceSettingsSave,
    FinanceSettingsToggleRule,
    InstitutionFieldMeta,
    InstitutionFieldOption,
)
from app.modules.audit.service import record_audit

_SCOPE_KEY = "finance_administration_settings"

_DEFAULTS: dict[str, Any] = {
    "invoice_prefix": "INV-{YYYY}-{#####}",
    "receipt_prefix": "RCT-{YYMM}-{####}",
    "financial_year_start": "april_1",
    "refund_approver": "finance_manager_principal",
    "late_fee_policy": "LF-2026",
    "default_payment_methods": "upi,card,net_banking,cash",
    "confirm_online_backend": True,
    "lock_posted_entries": True,
    "allow_installment_plans": True,
}

_FIELD_META = [
    InstitutionFieldMeta(key="invoice_prefix", label="Invoice prefix", field_type="text", required=True),
    InstitutionFieldMeta(key="receipt_prefix", label="Receipt prefix", field_type="text", required=True),
    InstitutionFieldMeta(key="financial_year_start", label="Financial year start", field_type="select", required=True),
    InstitutionFieldMeta(key="refund_approver", label="Refund approver", field_type="select", required=True),
    InstitutionFieldMeta(key="late_fee_policy", label="Late fee policy", field_type="select", required=True),
    InstitutionFieldMeta(
        key="default_payment_methods",
        label="Default payment methods",
        field_type="select",
        required=True,
    ),
]

_FIELD_OPTIONS: dict[str, list[InstitutionFieldOption]] = {
    "financial_year_start": [
        InstitutionFieldOption(value="april_1", label="1 April"),
        InstitutionFieldOption(value="january_1", label="1 January"),
    ],
    "refund_approver": [
        InstitutionFieldOption(value="finance_manager_principal", label="Finance Manager → Principal"),
        InstitutionFieldOption(value="principal", label="Principal"),
        InstitutionFieldOption(value="finance_manager", label="Finance Manager"),
    ],
    "late_fee_policy": [
        InstitutionFieldOption(value="LF-2026", label="LF-2026"),
        InstitutionFieldOption(value="LF-2025", label="LF-2025"),
    ],
    "default_payment_methods": [
        InstitutionFieldOption(value="upi,card,net_banking,cash", label="UPI, cards, net banking, cash"),
        InstitutionFieldOption(value="upi,card", label="UPI, cards"),
        InstitutionFieldOption(value="upi,net_banking", label="UPI, net banking"),
        InstitutionFieldOption(value="cash", label="Cash only"),
    ],
}

_TOGGLE_DEFS = (
    ("confirm_online_backend", "Confirm online payments through backend", "Required", "Requires server-side verification before posting."),
    ("lock_posted_entries", "Lock posted entries", "", "Prevent edits to ledger entries after posting."),
    ("allow_installment_plans", "Allow installment plans", "Needs approval", "Students may request payment plans subject to approval."),
)


async def _load_rules(tenant_id) -> dict[str, Any]:
    doc = await AcademicRegulation.find_one(
        Eq(AcademicRegulation.tenant_id, tenant_id),
        Eq(AcademicRegulation.scope_key, _SCOPE_KEY),
    )
    if doc and doc.rules:
        return {**_DEFAULTS, **doc.rules}
    merged = dict(_DEFAULTS)
    fee = await FinanceSettingsRecord.find_one(
        Eq(FinanceSettingsRecord.tenant_id, tenant_id),
        Eq(FinanceSettingsRecord.settings_domain, FinanceSettingsDomain.FEE.value),
        Eq(FinanceSettingsRecord.status, FinanceSettingStatus.ACTIVE),
    )
    if fee and fee.payload:
        prefix = fee.payload.get("invoice_number_prefix", "INV")
        merged["invoice_prefix"] = fee.payload.get("invoice_prefix") or f"{prefix}-{{YYYY}}-{{#####}}"
        merged["late_fee_policy"] = fee.payload.get("late_fee_policy_id") or merged["late_fee_policy"]
    receipt = await FinanceReceiptSettings.find_one(
        Eq(FinanceReceiptSettings.tenant_id, tenant_id),
        Eq(FinanceReceiptSettings.settings_domain, FinanceSettingsDomain.RECEIPT.value),
        Eq(FinanceReceiptSettings.status, FinanceSettingStatus.ACTIVE),
    )
    if receipt and receipt.payload:
        rp = receipt.payload.get("receipt_prefix", "RCT")
        merged["receipt_prefix"] = receipt.payload.get("receipt_prefix_format") or f"{rp}-{{YYMM}}-{{####}}"
        merged["confirm_online_backend"] = receipt.payload.get("require_verified_payment_for_receipt", True)
    payment = await FinancePaymentSettings.find_one(
        Eq(FinancePaymentSettings.tenant_id, tenant_id),
        Eq(FinancePaymentSettings.settings_domain, FinanceSettingsDomain.PAYMENT.value),
        Eq(FinancePaymentSettings.status, FinanceSettingStatus.ACTIVE),
    )
    if payment and payment.payload:
        merged["confirm_online_backend"] = payment.payload.get("confirm_online_via_backend", merged["confirm_online_backend"])
        merged["allow_installment_plans"] = payment.payload.get("partial_payments_allowed", merged["allow_installment_plans"])
    periods = await FinancialPeriod.find(Eq(FinancialPeriod.tenant_id, tenant_id)).sort("start_date").to_list()
    period = periods[0] if periods else None
    if period and period.start_date.month == 4:
        merged["financial_year_start"] = "april_1"
    elif period and period.start_date.month == 1:
        merged["financial_year_start"] = "january_1"
    workflow = await FinanceApprovalWorkflow.find_one(
        Eq(FinanceApprovalWorkflow.tenant_id, tenant_id),
        Eq(FinanceApprovalWorkflow.workflow_key, "refund"),
    )
    if workflow and workflow.label:
        label = workflow.label.lower()
        if "principal" in label and "finance" in label:
            merged["refund_approver"] = "finance_manager_principal"
    gateways = await PaymentGatewayConfiguration.find(Eq(PaymentGatewayConfiguration.tenant_id, tenant_id)).to_list()
    if gateways:
        methods: list[str] = []
        for gw in gateways:
            for method in gw.supported_methods or []:
                methods.append(str(method.value if hasattr(method, "value") else method).lower())
        if methods:
            merged["default_payment_methods"] = ",".join(dict.fromkeys(methods + ["cash"]))
    if not fee and not receipt and not payment:
        merged.setdefault("invoice_prefix", f"{DEFAULT_FEE.get('invoice_number_prefix', 'INV')}-{{YYYY}}-{{#####}}")
        merged.setdefault("receipt_prefix", f"{DEFAULT_RECEIPT.get('receipt_prefix', 'RCT')}-{{YYMM}}-{{####}}")
        merged["confirm_online_backend"] = DEFAULT_RECEIPT.get("require_verified_payment_for_receipt", True)
        merged["allow_installment_plans"] = DEFAULT_PAYMENT.get("partial_payments_allowed", True)
    return merged


def _coerce_form(rules: dict[str, Any]) -> FinanceSettingsFormValues:
    return FinanceSettingsFormValues(
        invoice_prefix=str(rules.get("invoice_prefix", _DEFAULTS["invoice_prefix"])),
        receipt_prefix=str(rules.get("receipt_prefix", _DEFAULTS["receipt_prefix"])),
        financial_year_start=str(rules.get("financial_year_start", _DEFAULTS["financial_year_start"])),
        refund_approver=str(rules.get("refund_approver", _DEFAULTS["refund_approver"])),
        late_fee_policy=str(rules.get("late_fee_policy", _DEFAULTS["late_fee_policy"])),
        default_payment_methods=str(rules.get("default_payment_methods", _DEFAULTS["default_payment_methods"])),
        confirm_online_backend=bool(rules.get("confirm_online_backend", True)),
        lock_posted_entries=bool(rules.get("lock_posted_entries", True)),
        allow_installment_plans=bool(rules.get("allow_installment_plans", True)),
    )


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


async def get_finance_settings_page(scope: AccessScope) -> FinanceSettingsPageRead:
    authorize(scope, Permission.FINANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    rules = await _load_rules(tenant_id)
    form = _coerce_form(rules)
    toggles = [
        FinanceSettingsToggleRule(
            key=key,
            label=label,
            description=description,
            badge_label=badge,
            enabled=bool(getattr(form, key)),
        )
        for key, label, badge, description in _TOGGLE_DEFS
    ]
    return FinanceSettingsPageRead(
        page_title="Finance Settings",
        page_subtitle="Numbering, approval and payment configuration",
        cancel_label="Cancel",
        save_label="Save",
        configuration_section_title="Finance configuration",
        controls_section_title="Controls",
        form=form,
        field_meta=_FIELD_META,
        field_options=_FIELD_OPTIONS,
        toggle_rules=toggles,
        generated_at=utcnow(),
    )


async def save_finance_settings_page(scope: AccessScope, payload: FinanceSettingsSave) -> FinanceSettingsPageRead:
    authorize(scope, Permission.FINANCE_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    rules = payload.form.model_dump(mode="json")
    await _persist_rules(scope, tenant_id, rules)
    await record_audit(
        actor_id=scope.user_id,
        action="finance.settings.page_updated",
        resource_type="academic_regulation",
        resource_id=_SCOPE_KEY,
        tenant_id=tenant_id,
    )
    return await get_finance_settings_page(scope)