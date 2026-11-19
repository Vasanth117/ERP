"""Statutory configuration, tax declarations and compliance."""

from datetime import date
from decimal import Decimal

from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.hr.enums import HrTaxDeclarationStatus, HrTaxFinancialYearStatus, HrTaxProofStatus
from app.modules.hr.hr_notification_dispatch import enqueue_hr_notification
from app.modules.hr.policy import (
    authorize_hr_statutory_manage,
    authorize_hr_statutory_read,
    authorize_hr_tax_manage,
    require_employee_tenant_scope,
    require_hr_tenant_scope,
)
from app.modules.hr.statutory_tax_models import (
    EmployeeTaxDeclaration,
    EmployeeTaxProfile,
    EmployeeTaxProof,
    EmployeeTaxReviewHistory,
    HrStatutoryComponent,
    HrStatutoryRuleVersion,
    HrTaxFinancialYear,
    HrTaxRegimeConfiguration,
    HrTaxSlab,
)
from app.modules.hr.statutory_tax_schemas import (
    ComplianceReport,
    EmployeeTaxProfileRead,
    EmployeeTaxProfileUpsert,
    StatutoryComponentRead,
    StatutoryComponentUpsert,
    StatutoryRuleVersionCreate,
    StatutoryRuleVersionRead,
    TaxDeclarationRead,
    TaxDeclarationReview,
    TaxDeclarationUpsert,
    TaxFinancialYearRead,
    TaxFinancialYearUpsert,
    TaxProofRead,
    TaxProofReview,
    TaxProofUpsert,
    TaxRegimeRead,
    TaxRegimeUpsert,
    TaxSlabRead,
    TaxSlabUpsert,
)


def _sum_declared(lines: dict) -> str:
    total = Decimal("0")
    for val in lines.values():
        if isinstance(val, dict) and "amount" in val:
            total += Decimal(str(val["amount"]))
        elif isinstance(val, (int, float, str)):
            try:
                total += Decimal(str(val))
            except Exception:
                continue
    return str(total.quantize(Decimal("0.01")))


async def upsert_statutory_component(scope: AccessScope, payload: StatutoryComponentUpsert) -> StatutoryComponentRead:
    authorize_hr_statutory_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    doc = await HrStatutoryComponent.find_one(
        Eq(HrStatutoryComponent.tenant_id, tenant_id),
        Eq(HrStatutoryComponent.component_code, payload.component_code),
    )
    if doc:
        doc.display_name = payload.display_name
        doc.component_kind = payload.component_kind
        doc.statutory_ref = payload.statutory_ref
        doc.employee_categories = payload.employee_categories
        doc.calculation_basis = payload.calculation_basis
        doc.eligible_salary_components = payload.eligible_salary_components
        doc.is_active = payload.is_active
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = HrStatutoryComponent(
            tenant_id=tenant_id,
            component_code=payload.component_code,
            display_name=payload.display_name,
            component_kind=payload.component_kind,
            statutory_ref=payload.statutory_ref,
            employee_categories=payload.employee_categories,
            calculation_basis=payload.calculation_basis,
            eligible_salary_components=payload.eligible_salary_components,
            is_active=payload.is_active,
            actor_id=scope.user_id,
        )
        await doc.insert()
    return StatutoryComponentRead.from_doc(doc)


async def list_statutory_components(scope: AccessScope) -> list[StatutoryComponentRead]:
    authorize_hr_statutory_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rows = await HrStatutoryComponent.find(Eq(HrStatutoryComponent.tenant_id, tenant_id)).to_list()
    return [StatutoryComponentRead.from_doc(r) for r in rows]


async def create_statutory_rule_version(scope: AccessScope, payload: StatutoryRuleVersionCreate) -> StatutoryRuleVersionRead:
    authorize_hr_statutory_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    cid = to_object_id(payload.component_id, "component_id")
    component = await HrStatutoryComponent.get(cid)
    if component is None or component.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Statutory component not found", status_code=404)
    next_ver = component.active_rule_version + 1
    row = HrStatutoryRuleVersion(
        tenant_id=tenant_id,
        component_id=component.id,
        component_code=component.component_code,
        version_number=next_ver,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        employee_rate_percent=payload.employee_rate_percent,
        employer_rate_percent=payload.employer_rate_percent,
        fixed_amount=payload.fixed_amount,
        threshold_min=payload.threshold_min,
        threshold_max=payload.threshold_max,
        exemptions=payload.exemptions,
        rounding_rule=payload.rounding_rule,
        actor_id=scope.user_id,
    )
    await row.insert()
    component.active_rule_version = next_ver
    component.updated_at = utcnow()
    await component.save()
    return StatutoryRuleVersionRead.from_doc(row)


async def list_statutory_rule_versions(scope: AccessScope, component_code: str | None = None) -> list[StatutoryRuleVersionRead]:
    authorize_hr_statutory_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    filters = [Eq(HrStatutoryRuleVersion.tenant_id, tenant_id)]
    if component_code:
        filters.append(Eq(HrStatutoryRuleVersion.component_code, component_code))
    rows = await HrStatutoryRuleVersion.find(*filters).sort(-HrStatutoryRuleVersion.version_number).to_list()
    return [StatutoryRuleVersionRead.from_doc(r) for r in rows]


async def upsert_tax_financial_year(scope: AccessScope, payload: TaxFinancialYearUpsert) -> TaxFinancialYearRead:
    authorize_hr_tax_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    doc = await HrTaxFinancialYear.find_one(Eq(HrTaxFinancialYear.tenant_id, tenant_id), Eq(HrTaxFinancialYear.fy_code, payload.fy_code))
    if doc:
        doc.label = payload.label
        doc.start_date = payload.start_date
        doc.end_date = payload.end_date
        doc.assessment_year = payload.assessment_year
        doc.status = payload.status
        doc.version += 1
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = HrTaxFinancialYear(
            tenant_id=tenant_id,
            fy_code=payload.fy_code,
            label=payload.label,
            start_date=payload.start_date,
            end_date=payload.end_date,
            assessment_year=payload.assessment_year,
            status=payload.status,
            actor_id=scope.user_id,
        )
        await doc.insert()
    return TaxFinancialYearRead.from_doc(doc)


async def list_tax_financial_years(scope: AccessScope) -> list[TaxFinancialYearRead]:
    authorize_hr_tax_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rows = await HrTaxFinancialYear.find(Eq(HrTaxFinancialYear.tenant_id, tenant_id)).to_list()
    return [TaxFinancialYearRead.from_doc(r) for r in rows]


async def upsert_tax_regime(scope: AccessScope, payload: TaxRegimeUpsert) -> TaxRegimeRead:
    authorize_hr_tax_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    fy_id = to_object_id(payload.financial_year_id, "financial_year_id")
    fy = await HrTaxFinancialYear.get(fy_id)
    if fy is None or fy.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Financial year not found", status_code=404)
    existing = await HrTaxRegimeConfiguration.find_one(
        Eq(HrTaxRegimeConfiguration.tenant_id, tenant_id),
        Eq(HrTaxRegimeConfiguration.financial_year_id, fy_id),
        Eq(HrTaxRegimeConfiguration.regime_code, payload.regime_code),
    )
    version = (existing.version + 1) if existing else 1
    row = HrTaxRegimeConfiguration(
        tenant_id=tenant_id,
        financial_year_id=fy_id,
        regime_code=payload.regime_code,
        display_name=payload.display_name,
        is_default=payload.is_default,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        rules=payload.rules,
        version=version,
        actor_id=scope.user_id,
    )
    await row.insert()
    return TaxRegimeRead.from_doc(row)


async def upsert_tax_slab(scope: AccessScope, payload: TaxSlabUpsert) -> TaxSlabRead:
    authorize_hr_tax_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    regime_id = to_object_id(payload.regime_configuration_id, "regime_configuration_id")
    regime = await HrTaxRegimeConfiguration.get(regime_id)
    if regime is None or regime.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Tax regime not found", status_code=404)
    existing = await HrTaxSlab.find_one(
        Eq(HrTaxSlab.tenant_id, tenant_id),
        Eq(HrTaxSlab.regime_configuration_id, regime_id),
        Eq(HrTaxSlab.slab_order, payload.slab_order),
        Eq(HrTaxSlab.effective_from, payload.effective_from),
    )
    if existing:
        existing.income_from = payload.income_from
        existing.income_to = payload.income_to
        existing.rate_percent = payload.rate_percent
        existing.rebate_amount = payload.rebate_amount
        existing.effective_to = payload.effective_to
        await existing.save()
        doc = existing
    else:
        doc = HrTaxSlab(
            tenant_id=tenant_id,
            regime_configuration_id=regime_id,
            slab_order=payload.slab_order,
            income_from=payload.income_from,
            income_to=payload.income_to,
            rate_percent=payload.rate_percent,
            rebate_amount=payload.rebate_amount,
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
            actor_id=scope.user_id,
        )
        await doc.insert()
    return TaxSlabRead.from_doc(doc)


async def upsert_employee_tax_profile(scope: AccessScope, payload: EmployeeTaxProfileUpsert) -> EmployeeTaxProfileRead:
    authorize_hr_tax_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    uid = to_object_id(payload.employee_user_id, "employee_user_id")
    doc = await EmployeeTaxProfile.find_one(Eq(EmployeeTaxProfile.tenant_id, tenant_id), Eq(EmployeeTaxProfile.employee_user_id, uid))
    if doc:
        doc.pan_number = payload.pan_number
        doc.aadhaar_masked = payload.aadhaar_masked
        doc.uan_number = payload.uan_number
        doc.esi_number = payload.esi_number
        doc.preferred_regime_code = payload.preferred_regime_code
        doc.updated_by = scope.user_id
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = EmployeeTaxProfile(
            tenant_id=tenant_id,
            employee_user_id=uid,
            pan_number=payload.pan_number,
            aadhaar_masked=payload.aadhaar_masked,
            uan_number=payload.uan_number,
            esi_number=payload.esi_number,
            preferred_regime_code=payload.preferred_regime_code,
            updated_by=scope.user_id,
        )
        await doc.insert()
    return EmployeeTaxProfileRead.from_doc(doc)


async def save_tax_declaration_draft(
    scope: AccessScope,
    employee_user_id: str,
    payload: TaxDeclarationUpsert,
    *,
    self_service: bool,
) -> TaxDeclarationRead:
    uid = to_object_id(employee_user_id, "employee_user_id")
    if self_service:
        if scope.user_id != uid:
            raise AppError(code="FORBIDDEN", message="Cannot edit another employee declaration", status_code=403)
        tenant_id = require_employee_tenant_scope(scope)
    else:
        authorize_hr_tax_manage(scope)
        tenant_id = require_hr_tenant_scope(scope)
    fy_id = to_object_id(payload.financial_year_id, "financial_year_id")
    fy = await HrTaxFinancialYear.get(fy_id)
    if fy is None or fy.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Financial year not found", status_code=404)
    if fy.status == HrTaxFinancialYearStatus.CLOSED:
        raise AppError(code="CONFLICT", message="Financial year is closed", status_code=409)
    doc = await EmployeeTaxDeclaration.find_one(
        Eq(EmployeeTaxDeclaration.tenant_id, tenant_id),
        Eq(EmployeeTaxDeclaration.employee_user_id, uid),
        Eq(EmployeeTaxDeclaration.financial_year_id, fy_id),
    )
    total = _sum_declared(payload.declaration_lines)
    if doc:
        if doc.status not in {HrTaxDeclarationStatus.DRAFT, HrTaxDeclarationStatus.RETURNED}:
            raise AppError(code="CONFLICT", message="Declaration is not editable", status_code=409)
        doc.regime_code = payload.regime_code
        doc.declaration_lines = payload.declaration_lines
        doc.total_declared_deductions = total
        doc.employee_note = payload.employee_note
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = EmployeeTaxDeclaration(
            tenant_id=tenant_id,
            employee_user_id=uid,
            financial_year_id=fy_id,
            fy_code=fy.fy_code,
            regime_code=payload.regime_code,
            declaration_lines=payload.declaration_lines,
            total_declared_deductions=total,
            employee_note=payload.employee_note,
        )
        await doc.insert()
    return TaxDeclarationRead.from_doc(doc)


async def submit_tax_declaration(scope: AccessScope, declaration_id: str, *, self_service: bool) -> TaxDeclarationRead:
    tenant_id = require_employee_tenant_scope(scope) if self_service else require_hr_tenant_scope(scope)
    did = to_object_id(declaration_id, "declaration_id")
    doc = await EmployeeTaxDeclaration.get(did)
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Declaration not found", status_code=404)
    if self_service and scope.user_id != doc.employee_user_id:
        raise AppError(code="FORBIDDEN", message="Declaration access denied", status_code=403)
    if doc.status not in {HrTaxDeclarationStatus.DRAFT, HrTaxDeclarationStatus.RETURNED}:
        raise AppError(code="CONFLICT", message="Declaration cannot be submitted", status_code=409)
    doc.status = HrTaxDeclarationStatus.SUBMITTED
    doc.submitted_at = utcnow()
    doc.updated_at = utcnow()
    await doc.save()
    await EmployeeTaxReviewHistory(
        tenant_id=tenant_id,
        declaration_id=doc.id,
        action="submitted",
        from_status=HrTaxDeclarationStatus.DRAFT.value,
        to_status=doc.status.value,
        actor_id=scope.user_id,
    ).insert()
    return TaxDeclarationRead.from_doc(doc)


async def review_tax_declaration(scope: AccessScope, declaration_id: str, payload: TaxDeclarationReview) -> TaxDeclarationRead:
    authorize_hr_tax_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    did = to_object_id(declaration_id, "declaration_id")
    doc = await EmployeeTaxDeclaration.get(did)
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Declaration not found", status_code=404)
    if doc.status not in {HrTaxDeclarationStatus.SUBMITTED, HrTaxDeclarationStatus.UNDER_REVIEW}:
        raise AppError(code="CONFLICT", message="Declaration is not under review", status_code=409)
    prev = doc.status.value
    if payload.action == "approve":
        doc.status = HrTaxDeclarationStatus.APPROVED
        doc.approved_snapshot = payload.approved_snapshot or {"declaration_lines": doc.declaration_lines}
        income = Decimal(str(doc.approved_snapshot.get("annual_taxable_income", "0")))
        slabs = await HrTaxSlab.find(Eq(HrTaxSlab.tenant_id, tenant_id)).sort(HrTaxSlab.slab_order).to_list()
        annual_tax = Decimal("0")
        remaining = income
        for slab in slabs:
            slab_from = Decimal(slab.income_from)
            slab_to = Decimal(slab.income_to) if slab.income_to else income
            if remaining <= 0:
                break
            taxable = min(remaining, max(Decimal("0"), slab_to - slab_from))
            annual_tax += taxable * Decimal(slab.rate_percent) / Decimal("100")
            remaining -= taxable
        doc.approved_snapshot["annual_tax_estimate"] = str(annual_tax.quantize(Decimal("0.01")))
        doc.approved_snapshot["monthly_tds_estimate"] = str((annual_tax / Decimal("12")).quantize(Decimal("0.01")))
    elif payload.action == "reject":
        doc.status = HrTaxDeclarationStatus.REJECTED
    else:
        doc.status = HrTaxDeclarationStatus.RETURNED
    doc.reviewer_id = scope.user_id
    doc.reviewer_note = payload.reviewer_note
    doc.reviewed_at = utcnow()
    doc.updated_at = utcnow()
    await doc.save()
    await EmployeeTaxReviewHistory(
        tenant_id=tenant_id,
        declaration_id=doc.id,
        action=payload.action,
        from_status=prev,
        to_status=doc.status.value,
        note=payload.reviewer_note,
        actor_id=scope.user_id,
    ).insert()
    await enqueue_hr_notification(
        tenant_id,
        event_type="hr.tax.declaration_reviewed",
        aggregate_type="employee_tax_declaration",
        aggregate_id=str(doc.id),
        title="Tax declaration update",
        body=f"Your tax declaration for {doc.fy_code} is now {doc.status.value}",
        recipient_user_id=doc.employee_user_id,
        dedupe_key=f"hr:tax_decl:{doc.id}:{doc.status.value}",
    )
    return TaxDeclarationRead.from_doc(doc)


async def add_tax_proof(
    scope: AccessScope,
    declaration_id: str,
    payload: TaxProofUpsert,
    *,
    self_service: bool,
) -> TaxProofRead:
    tenant_id = require_hr_tenant_scope(scope)
    did = to_object_id(declaration_id, "declaration_id")
    doc = await EmployeeTaxDeclaration.get(did)
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Declaration not found", status_code=404)
    if self_service:
        if scope.user_id != doc.employee_user_id:
            raise AppError(code="FORBIDDEN", message="Proof access denied", status_code=403)
    else:
        authorize_hr_tax_manage(scope)
    proof = EmployeeTaxProof(
        tenant_id=tenant_id,
        declaration_id=doc.id,
        employee_user_id=doc.employee_user_id,
        proof_category=payload.proof_category,
        claimed_amount=payload.claimed_amount,
        document_ref=payload.document_ref,
        storage_key=payload.storage_key,
    )
    await proof.insert()
    return TaxProofRead.from_doc(proof)


async def review_tax_proof(scope: AccessScope, proof_id: str, payload: TaxProofReview) -> TaxProofRead:
    authorize_hr_tax_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    pid = to_object_id(proof_id, "proof_id")
    proof = await EmployeeTaxProof.get(pid)
    if proof is None or proof.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Proof not found", status_code=404)
    prev = proof.status.value
    if payload.action == "verify":
        proof.status = HrTaxProofStatus.VERIFIED
        proof.verified_amount = payload.verified_amount or proof.claimed_amount
    elif payload.action == "reject":
        proof.status = HrTaxProofStatus.REJECTED
    else:
        proof.status = HrTaxProofStatus.RETURNED
    proof.reviewer_id = scope.user_id
    proof.reviewer_note = payload.reviewer_note
    proof.updated_at = utcnow()
    await proof.save()
    await EmployeeTaxReviewHistory(
        tenant_id=tenant_id,
        declaration_id=proof.declaration_id,
        proof_id=proof.id,
        action=f"proof_{payload.action}",
        from_status=prev,
        to_status=proof.status.value,
        note=payload.reviewer_note,
        actor_id=scope.user_id,
    ).insert()
    return TaxProofRead.from_doc(proof)


async def list_tax_declarations(scope: AccessScope, employee_user_id: str | None = None) -> list[TaxDeclarationRead]:
    authorize_hr_tax_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    filters = [Eq(EmployeeTaxDeclaration.tenant_id, tenant_id)]
    if employee_user_id:
        filters.append(Eq(EmployeeTaxDeclaration.employee_user_id, to_object_id(employee_user_id, "employee_user_id")))
    rows = await EmployeeTaxDeclaration.find(*filters).sort(-EmployeeTaxDeclaration.updated_at).to_list()
    return [TaxDeclarationRead.from_doc(r) for r in rows]


async def compliance_report(scope: AccessScope) -> ComplianceReport:
    authorize_hr_statutory_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    report = ComplianceReport()
    employees = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    active_ids = {e.user_id for e in employees}
    declarations = await EmployeeTaxDeclaration.find(Eq(EmployeeTaxDeclaration.tenant_id, tenant_id)).to_list()
    declared_users = {d.employee_user_id for d in declarations if d.status == HrTaxDeclarationStatus.APPROVED}
    report.missing_tax_declarations = len(active_ids - declared_users)
    proofs = await EmployeeTaxProof.find(Eq(EmployeeTaxProof.tenant_id, tenant_id)).to_list()
    for p in proofs:
        if p.status == HrTaxProofStatus.PENDING:
            report.pending_proofs += 1
        elif p.status == HrTaxProofStatus.REJECTED:
            report.rejected_proofs += 1
    fys = await HrTaxFinancialYear.find(Eq(HrTaxFinancialYear.tenant_id, tenant_id)).to_list()
    report.open_financial_years = [fy.fy_code for fy in fys if fy.status != HrTaxFinancialYearStatus.CLOSED]
    return report