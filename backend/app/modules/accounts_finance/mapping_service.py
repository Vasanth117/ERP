"""Versioned accounting mapping rules."""

import uuid
from typing import Any

from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.accounts_finance.phase9_models import AccountingMappingRule, AccountingMappingVersion, ChartOfAccount
from app.modules.accounts_finance.policy import authorize_finance_gl_manage, authorize_finance_gl_read, require_finance_tenant_scope
from app.modules.college_admin.security_admin_service import append_institution_audit


async def create_mapping_version(scope: AccessScope, label: str) -> dict:
    authorize_finance_gl_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    version_id = f"mapv_{uuid.uuid4().hex[:10]}"
    doc = AccountingMappingVersion(tenant_id=tenant_id, version_id=version_id, label=label, active=False)
    await doc.insert()
    return {"version_id": version_id, "label": label}


async def add_mapping_rule(scope: AccessScope, version_id: str, payload: dict[str, Any]) -> dict:
    authorize_finance_gl_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    version = await AccountingMappingVersion.find_one(
        Eq(AccountingMappingVersion.tenant_id, tenant_id),
        Eq(AccountingMappingVersion.version_id, version_id),
    )
    if version is None:
        raise AppError(code="NOT_FOUND", message="Mapping version not found", status_code=404)
    for code in (payload["debit_account_code"], payload["credit_account_code"]):
        acct = await ChartOfAccount.find_one(Eq(ChartOfAccount.tenant_id, tenant_id), Eq(ChartOfAccount.account_code, code))
        if acct is None or not acct.active:
            raise AppError(code="VALIDATION_ERROR", message=f"Invalid account {code}", status_code=400)
    rule_id = f"rule_{uuid.uuid4().hex[:10]}"
    rule = AccountingMappingRule(
        tenant_id=tenant_id,
        rule_id=rule_id,
        version_id=version_id,
        event_type=payload["event_type"],
        debit_account_code=payload["debit_account_code"],
        credit_account_code=payload["credit_account_code"],
        description=payload.get("description"),
    )
    await rule.insert()
    return {"rule_id": rule_id, "event_type": rule.event_type}


async def activate_mapping_version(scope: AccessScope, version_id: str) -> dict:
    authorize_finance_gl_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    version = await AccountingMappingVersion.find_one(
        Eq(AccountingMappingVersion.tenant_id, tenant_id),
        Eq(AccountingMappingVersion.version_id, version_id),
    )
    if version is None:
        raise AppError(code="NOT_FOUND", message="Mapping version not found", status_code=404)
    rules = await AccountingMappingRule.find(
        Eq(AccountingMappingRule.tenant_id, tenant_id),
        Eq(AccountingMappingRule.version_id, version_id),
        Eq(AccountingMappingRule.active, True),
    ).count()
    if rules == 0:
        raise AppError(code="VALIDATION_ERROR", message="Version has no active rules", status_code=400)
    others = await AccountingMappingVersion.find(Eq(AccountingMappingVersion.tenant_id, tenant_id)).to_list()
    now = utcnow()
    for other in others:
        other.active = other.version_id == version_id
        if other.active:
            other.activated_at = now
            other.approved_by = scope.user_id
        await other.save()
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="finance.gl.mapping.activate",
        module="accounts_finance",
        resource_type="accounting_mapping_version",
        resource_id=version_id,
    )
    return {"version_id": version_id, "active": True}


async def get_active_rule(tenant_id, event_type: str) -> AccountingMappingRule | None:
    active = await AccountingMappingVersion.find_one(
        Eq(AccountingMappingVersion.tenant_id, tenant_id),
        Eq(AccountingMappingVersion.active, True),
    )
    if active is None:
        return None
    return await AccountingMappingRule.find_one(
        Eq(AccountingMappingRule.tenant_id, tenant_id),
        Eq(AccountingMappingRule.version_id, active.version_id),
        Eq(AccountingMappingRule.event_type, event_type),
        Eq(AccountingMappingRule.active, True),
    )


async def seed_default_mappings(scope: AccessScope, version_id: str | None = None) -> dict:
    """Default student-fee mappings after chart seed."""
    authorize_finance_gl_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    if version_id is None:
        ver = await create_mapping_version(scope, "Default student fee mappings")
        version_id = ver["version_id"]
    defaults = [
        ("fee_invoice", "1100", "4100"),
        ("verified_payment", "1000", "1100"),
        ("scholarship_credit", "5100", "1100"),
        ("concession_credit", "5100", "1100"),
        ("fee_waiver", "5100", "1100"),
        ("late_fee", "1100", "5200"),
        ("late_fee_waiver", "5200", "1100"),
        ("refund", "1150", "1000"),
        ("payment_reversal", "1100", "1000"),
        ("adjustment", "5100", "1100"),
    ]
    created = 0
    for event, debit, credit in defaults:
        await add_mapping_rule(scope, version_id, {"event_type": event, "debit_account_code": debit, "credit_account_code": credit})
        created += 1
    await activate_mapping_version(scope, version_id)
    return {"version_id": version_id, "rules_created": created}


async def list_mapping_versions(scope: AccessScope) -> list[dict]:
    authorize_finance_gl_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    rows = await AccountingMappingVersion.find(Eq(AccountingMappingVersion.tenant_id, tenant_id)).to_list()
    return [{"version_id": r.version_id, "label": r.label, "active": r.active, "activated_at": r.activated_at} for r in rows]