"""Finance settings dashboard, versioning and approval workflows."""

import uuid
from datetime import date
from typing import Any

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission, permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.accounts_finance.phase12_enums import FinanceSettingStatus, FinanceSettingsDomain
from app.modules.accounts_finance.phase12_models import (
    FinanceApprovalWorkflow,
    FinanceApprovalWorkflowVersion,
    FinancePaymentSettings,
    FinanceReceiptSettings,
    FinanceSettingHistory,
    FinanceSettingsRecord,
)
from app.modules.accounts_finance.phase3_models import PaymentGatewayConfiguration
from app.modules.accounts_finance.policy import (
    authorize_finance_settings_approve,
    authorize_finance_settings_manage,
    authorize_finance_settings_read,
    require_finance_tenant_scope,
)
from app.modules.accounts_finance.phase4_models import PaymentReceiptNumberSequence
from app.modules.college_admin.finance_admin_models import FinancialPeriod
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.college_admin.finance_ext_models import InstitutionVendorRecord

DOMAIN_MODEL = {
    FinanceSettingsDomain.GENERAL.value: FinanceSettingsRecord,
    FinanceSettingsDomain.FEE.value: FinanceSettingsRecord,
    FinanceSettingsDomain.PAYMENT.value: FinancePaymentSettings,
    FinanceSettingsDomain.RECEIPT.value: FinanceReceiptSettings,
    FinanceSettingsDomain.SCHOLARSHIP.value: FinanceSettingsRecord,
    FinanceSettingsDomain.INSTALLMENT.value: FinanceSettingsRecord,
    FinanceSettingsDomain.REFUND.value: FinanceSettingsRecord,
    FinanceSettingsDomain.ACCOUNTING.value: FinanceSettingsRecord,
    FinanceSettingsDomain.BUDGET.value: FinanceSettingsRecord,
    FinanceSettingsDomain.TAX.value: FinanceSettingsRecord,
    FinanceSettingsDomain.REPORTING.value: FinanceSettingsRecord,
}

DEFAULT_GENERAL = {
    "currency": "INR",
    "currency_precision": 2,
    "rounding_rule": "half_up",
    "finance_contact_email": None,
}

DEFAULT_FEE = {
    "invoice_number_prefix": "INV",
    "due_date_offset_days": 15,
    "publish_on_issue": True,
}

DEFAULT_PAYMENT = {
    "allow_online": True,
    "allow_offline": True,
    "require_offline_verification": True,
    "partial_payments_allowed": True,
    "payment_expiry_minutes": 30,
}

DEFAULT_RECEIPT = {
    "receipt_prefix": "RCP",
    "reuse_numbers": False,
    "require_verified_payment_for_receipt": True,
}

FINANCE_ROLE_CATALOG = {
    "finance_administrator": [
        Permission.FINANCE_SETTINGS_MANAGE,
        Permission.FINANCE_SETTINGS_APPROVE,
        Permission.FINANCE_ADMIN_MANAGE,
    ],
    "finance_manager": [
        Permission.FINANCE_DASHBOARD_READ,
        Permission.FINANCE_GL_APPROVE,
        Permission.FINANCE_PERIOD_CLOSE,
        Permission.FINANCE_SETTINGS_APPROVE,
    ],
    "fee_administrator": [Permission.FINANCE_STRUCTURE_MANAGE, Permission.FINANCE_INVOICE_ISSUE],
    "cashier": [Permission.FINANCE_OFFLINE_COLLECT, Permission.FINANCE_RECEIPT_ISSUE],
    "finance_auditor": [Permission.FINANCE_AUDIT_READ, Permission.FINANCE_AUDIT_INVESTIGATE, Permission.FINANCE_AUDIT_EXPORT],
    "read_only_viewer": [Permission.FINANCE_DASHBOARD_READ, Permission.FINANCE_REPORT_READ, Permission.FINANCE_SETTINGS_READ],
}


async def _settings_history(tenant_id, domain: str, version_id: str, from_status: str | None, to_status: str, actor_id, note: str | None = None) -> None:
    await FinanceSettingHistory(
        tenant_id=tenant_id,
        history_id=f"fsh_{uuid.uuid4().hex[:12]}",
        settings_domain=domain,
        version_id=version_id,
        from_status=from_status,
        to_status=to_status,
        actor_id=actor_id,
        note=note,
    ).insert()


async def settings_dashboard(scope: AccessScope) -> dict:
    authorize_finance_settings_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    periods = await FinancialPeriod.find(Eq(FinancialPeriod.tenant_id, tenant_id)).to_list()
    gateways = await PaymentGatewayConfiguration.find(Eq(PaymentGatewayConfiguration.tenant_id, tenant_id)).to_list()
    vendors = await InstitutionVendorRecord.find(Eq(InstitutionVendorRecord.tenant_id, tenant_id)).count()
    active_settings = await FinanceSettingsRecord.find(
        Eq(FinanceSettingsRecord.tenant_id, tenant_id),
        Eq(FinanceSettingsRecord.status, FinanceSettingStatus.ACTIVE),
    ).count()
    pending = await FinanceSettingsRecord.find(
        Eq(FinanceSettingsRecord.tenant_id, tenant_id),
        Eq(FinanceSettingsRecord.status, FinanceSettingStatus.UNDER_REVIEW),
    ).count()
    staff_perms = sorted(permissions_for_role(Role.FINANCE_STAFF))
    return {
        "open_financial_periods": sum(1 for p in periods if not p.locked and p.status.value == "open"),
        "closed_financial_periods": sum(1 for p in periods if p.locked or p.status.value == "closed"),
        "active_payment_gateways": sum(1 for g in gateways if g.active),
        "payment_methods_configured": len(gateways),
        "receipt_sequences": await PaymentReceiptNumberSequence.find(Eq(PaymentReceiptNumberSequence.tenant_id, tenant_id)).count(),
        "active_finance_settings_versions": active_settings,
        "pending_configuration_reviews": pending,
        "registered_vendors": vendors,
        "finance_staff_permission_count": len(staff_perms),
        "finance_role_catalog": list(FINANCE_ROLE_CATALOG.keys()),
        "operating_status": "active",
    }


async def create_settings_draft(scope: AccessScope, domain: str, payload: dict[str, Any]) -> dict:
    authorize_finance_settings_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    if domain not in DOMAIN_MODEL:
        raise AppError(code="VALIDATION_ERROR", message="Unknown settings domain", status_code=400)
    version_id = f"fsv_{uuid.uuid4().hex[:10]}"
    model = DOMAIN_MODEL[domain]
    doc = model(
        tenant_id=tenant_id,
        settings_domain=domain,
        version_id=version_id,
        status=FinanceSettingStatus.DRAFT,
        payload=payload,
        change_note=payload.get("change_note"),
        created_by=scope.user_id,
    )
    await doc.insert()
    await _settings_history(tenant_id, domain, version_id, None, doc.status.value, scope.user_id)
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="finance.settings.draft",
        module="accounts_finance",
        resource_type="finance_settings",
        resource_id=f"{domain}:{version_id}",
    )
    return {"domain": domain, "version_id": version_id, "status": doc.status.value}


async def submit_settings_version(scope: AccessScope, domain: str, version_id: str) -> dict:
    authorize_finance_settings_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    doc = await _get_version(tenant_id, domain, version_id)
    if doc.status != FinanceSettingStatus.DRAFT:
        raise AppError(code="CONFLICT", message="Only draft versions can be submitted", status_code=409)
    prev = doc.status.value
    doc.status = FinanceSettingStatus.UNDER_REVIEW
    doc.updated_at = utcnow()
    await doc.save()
    await _settings_history(tenant_id, domain, version_id, prev, doc.status.value, scope.user_id)
    return {"version_id": version_id, "status": doc.status.value}


async def approve_settings_version(scope: AccessScope, domain: str, version_id: str) -> dict:
    authorize_finance_settings_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    doc = await _get_version(tenant_id, domain, version_id)
    if doc.status != FinanceSettingStatus.UNDER_REVIEW:
        raise AppError(code="CONFLICT", message="Version not under review", status_code=409)
    prev = doc.status.value
    doc.status = FinanceSettingStatus.APPROVED
    doc.approved_by = scope.user_id
    doc.updated_at = utcnow()
    await doc.save()
    await _settings_history(tenant_id, domain, version_id, prev, doc.status.value, scope.user_id)
    return {"version_id": version_id, "status": doc.status.value}


async def activate_settings_version(scope: AccessScope, domain: str, version_id: str, *, effective_from: date | None = None) -> dict:
    authorize_finance_settings_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    doc = await _get_version(tenant_id, domain, version_id)
    if doc.status not in (FinanceSettingStatus.APPROVED, FinanceSettingStatus.SCHEDULED):
        raise AppError(code="CONFLICT", message="Version must be approved before activation", status_code=409)
    model = DOMAIN_MODEL[domain]
    actives = await model.find(
        Eq(model.tenant_id, tenant_id),
        Eq(model.settings_domain, domain),
        Eq(model.status, FinanceSettingStatus.ACTIVE),
    ).to_list()
    for old in actives:
        old.status = FinanceSettingStatus.SUPERSEDED
        old.superseded_by = version_id
        old.updated_at = utcnow()
        await old.save()
    doc.status = FinanceSettingStatus.ACTIVE
    doc.effective_from = effective_from or date.today()
    doc.updated_at = utcnow()
    await doc.save()
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="finance.settings.activate",
        module="accounts_finance",
        resource_type="finance_settings",
        resource_id=f"{domain}:{version_id}",
    )
    return {"version_id": version_id, "status": doc.status.value}


async def get_active_settings(scope: AccessScope, domain: str) -> dict:
    authorize_finance_settings_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    model = DOMAIN_MODEL[domain]
    doc = await model.find_one(
        Eq(model.tenant_id, tenant_id),
        Eq(model.settings_domain, domain),
        Eq(model.status, FinanceSettingStatus.ACTIVE),
    )
    if doc is None:
        defaults = {
            FinanceSettingsDomain.GENERAL.value: DEFAULT_GENERAL,
            FinanceSettingsDomain.FEE.value: DEFAULT_FEE,
            FinanceSettingsDomain.PAYMENT.value: DEFAULT_PAYMENT,
            FinanceSettingsDomain.RECEIPT.value: DEFAULT_RECEIPT,
        }.get(domain, {})
        return {"domain": domain, "status": "default", "payload": defaults}
    return {"domain": domain, "version_id": doc.version_id, "status": doc.status.value, "payload": doc.payload, "effective_from": doc.effective_from}


async def _get_version(tenant_id, domain: str, version_id: str):
    model = DOMAIN_MODEL[domain]
    doc = await model.find_one(Eq(model.tenant_id, tenant_id), Eq(model.settings_domain, domain), Eq(model.version_id, version_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Settings version not found", status_code=404)
    return doc


async def upsert_approval_workflow(scope: AccessScope, workflow_key: str, label: str, category: str) -> dict:
    authorize_finance_settings_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    doc = await FinanceApprovalWorkflow.find_one(Eq(FinanceApprovalWorkflow.tenant_id, tenant_id), Eq(FinanceApprovalWorkflow.workflow_key, workflow_key))
    if doc is None:
        doc = FinanceApprovalWorkflow(tenant_id=tenant_id, workflow_key=workflow_key, label=label, transaction_category=category)
        await doc.insert()
    else:
        doc.label = label
        doc.transaction_category = category
        await doc.save()
    return {"workflow_key": workflow_key}


async def create_workflow_version(scope: AccessScope, workflow_key: str, stages: list[dict], rules: dict | None = None) -> dict:
    authorize_finance_settings_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    version_id = f"wfv_{uuid.uuid4().hex[:10]}"
    await FinanceApprovalWorkflowVersion(
        tenant_id=tenant_id,
        version_id=version_id,
        workflow_key=workflow_key,
        stages=stages,
        rules=rules or {},
        created_by=scope.user_id,
    ).insert()
    return {"workflow_key": workflow_key, "version_id": version_id}


async def list_finance_roles(scope: AccessScope) -> dict:
    authorize_finance_settings_read(scope)
    require_finance_tenant_scope(scope)
    return {
        "platform_roles": [Role.FINANCE_STAFF.value],
        "catalog_roles": FINANCE_ROLE_CATALOG,
        "note": "Authoritative grants remain on User.role and Permission enumeration; catalog is advisory for assignment UI.",
    }