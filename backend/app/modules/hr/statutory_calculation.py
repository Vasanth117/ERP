"""Resolve effective-dated statutory and tax rules for payroll."""

from datetime import date
from decimal import Decimal
from typing import Any

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, LTE

from app.modules.college_admin.hr_admin_models import PayrollConfiguration
from app.modules.hr.enums import HrTaxDeclarationStatus
from app.modules.hr.statutory_tax_models import (
    EmployeeTaxDeclaration,
    HrStatutoryComponent,
    HrStatutoryRuleVersion,
)


def _d(value: str | float | int) -> Decimal:
    return Decimal(str(value))


async def _legacy_statutory_rates(tenant_id: PydanticObjectId) -> dict[str, str]:
    cfg = await PayrollConfiguration.find_one(Eq(PayrollConfiguration.tenant_id, tenant_id))
    if cfg is None:
        return {}
    raw = (cfg.confidential_config or {}).get("statutory_rates", {})
    return {str(k): str(v) for k, v in raw.items()}


def _category_applies(component: HrStatutoryComponent, employee_category: str | None) -> bool:
    if not component.employee_categories:
        return True
    if not employee_category:
        return True
    return employee_category in component.employee_categories


async def resolve_statutory_rates_for_employee(
    *,
    tenant_id: PydanticObjectId,
    as_of: date,
    employee_category: str | None,
    employee_user_id: PydanticObjectId | None = None,
) -> tuple[dict[str, str], list[str], dict[str, Any]]:
    """Returns rates map (statutory_ref -> percent string), warnings, and metadata for payroll snapshot."""
    warnings: list[str] = []
    refs: dict[str, Any] = {"rule_versions": [], "source": "statutory_configuration"}
    rates: dict[str, str] = {}

    components = await HrStatutoryComponent.find(
        Eq(HrStatutoryComponent.tenant_id, tenant_id),
        Eq(HrStatutoryComponent.is_active, True),
    ).to_list()
    if not components:
        legacy = await _legacy_statutory_rates(tenant_id)
        if not legacy:
            warnings.append("missing_statutory_configuration")
        refs["source"] = "payroll_configuration_legacy"
        return legacy, warnings, refs

    for component in components:
        if not _category_applies(component, employee_category):
            continue
        rule = await HrStatutoryRuleVersion.find(
            Eq(HrStatutoryRuleVersion.tenant_id, tenant_id),
            Eq(HrStatutoryRuleVersion.component_id, component.id),
            LTE(HrStatutoryRuleVersion.effective_from, as_of),
        ).sort(-HrStatutoryRuleVersion.version_number).first_or_none()
        if rule is None:
            warnings.append(f"missing_rule_version:{component.component_code}")
            continue
        if rule.effective_to and rule.effective_to < as_of:
            warnings.append(f"expired_rule:{component.component_code}")
            continue
        rates[component.statutory_ref] = rule.employee_rate_percent or rule.employer_rate_percent or "0"
        if rule.employer_rate_percent and rule.employer_rate_percent != "0":
            rates[f"{component.statutory_ref}_employer"] = rule.employer_rate_percent
        refs["rule_versions"].append(
            {
                "component_code": component.component_code,
                "statutory_ref": component.statutory_ref,
                "version_number": rule.version_number,
                "effective_from": rule.effective_from.isoformat(),
            }
        )

    if employee_user_id is not None:
        decl = await EmployeeTaxDeclaration.find(
            Eq(EmployeeTaxDeclaration.tenant_id, tenant_id),
            Eq(EmployeeTaxDeclaration.employee_user_id, employee_user_id),
            Eq(EmployeeTaxDeclaration.status, HrTaxDeclarationStatus.APPROVED),
        ).sort(-EmployeeTaxDeclaration.updated_at).first_or_none()
        if decl is None:
            warnings.append("missing_tax_declaration")
        else:
            refs["tax_declaration_id"] = str(decl.id)
            refs["tax_regime"] = decl.regime_code
            monthly_tds = decl.approved_snapshot.get("monthly_tds_estimate")
            if monthly_tds:
                rates["income_tax_tds"] = str(monthly_tds)

    if not rates:
        legacy = await _legacy_statutory_rates(tenant_id)
        rates.update(legacy)
        refs["source"] = "mixed_or_legacy"
        if not legacy:
            warnings.append("missing_statutory_configuration")

    return rates, warnings, refs


async def load_statutory_rates(tenant_id: PydanticObjectId, as_of: date | None = None) -> dict[str, str]:
    """Tenant-wide rates for payroll run defaults (category-agnostic)."""
    target = as_of or date.today()
    rates, _, _ = await resolve_statutory_rates_for_employee(
        tenant_id=tenant_id,
        as_of=target,
        employee_category=None,
        employee_user_id=None,
    )
    return rates