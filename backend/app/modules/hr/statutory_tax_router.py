"""Statutory payroll and tax configuration routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.hr.deps import hr_staff_user
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
from app.modules.hr.statutory_tax_service import (
    add_tax_proof,
    compliance_report,
    create_statutory_rule_version,
    list_statutory_components,
    list_statutory_rule_versions,
    list_tax_declarations,
    list_tax_financial_years,
    review_tax_declaration,
    review_tax_proof,
    save_tax_declaration_draft,
    submit_tax_declaration,
    upsert_employee_tax_profile,
    upsert_statutory_component,
    upsert_tax_financial_year,
    upsert_tax_regime,
    upsert_tax_slab,
)

router = APIRouter(prefix="/statutory-tax", tags=["hr-statutory-tax"])


@router.post("/components", response_model=ApiResponse[StatutoryComponentRead])
async def upsert_component_route(payload: StatutoryComponentUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await upsert_statutory_component(scope, payload), request_id=get_request_id())


@router.get("/components", response_model=ApiResponse[list[StatutoryComponentRead]])
async def list_components_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await list_statutory_components(scope), request_id=get_request_id())


@router.post("/rule-versions", response_model=ApiResponse[StatutoryRuleVersionRead])
async def create_rule_route(payload: StatutoryRuleVersionCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await create_statutory_rule_version(scope, payload), request_id=get_request_id())


@router.get("/rule-versions", response_model=ApiResponse[list[StatutoryRuleVersionRead]])
async def list_rules_route(scope: Annotated[AccessScope, Depends(get_access_scope)], component_code: str | None = None, _: Annotated[User, Depends(hr_staff_user)] = None):
    return success_response(await list_statutory_rule_versions(scope, component_code), request_id=get_request_id())


@router.post("/financial-years", response_model=ApiResponse[TaxFinancialYearRead])
async def upsert_fy_route(payload: TaxFinancialYearUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await upsert_tax_financial_year(scope, payload), request_id=get_request_id())


@router.get("/financial-years", response_model=ApiResponse[list[TaxFinancialYearRead]])
async def list_fy_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await list_tax_financial_years(scope), request_id=get_request_id())


@router.post("/regimes", response_model=ApiResponse[TaxRegimeRead])
async def upsert_regime_route(payload: TaxRegimeUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await upsert_tax_regime(scope, payload), request_id=get_request_id())


@router.post("/slabs", response_model=ApiResponse[TaxSlabRead])
async def upsert_slab_route(payload: TaxSlabUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await upsert_tax_slab(scope, payload), request_id=get_request_id())


@router.post("/employee-tax-profiles", response_model=ApiResponse[EmployeeTaxProfileRead])
async def upsert_tax_profile_route(payload: EmployeeTaxProfileUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await upsert_employee_tax_profile(scope, payload), request_id=get_request_id())


@router.get("/declarations", response_model=ApiResponse[list[TaxDeclarationRead]])
async def list_declarations_route(scope: Annotated[AccessScope, Depends(get_access_scope)], employee_user_id: str | None = None, _: Annotated[User, Depends(hr_staff_user)] = None):
    return success_response(await list_tax_declarations(scope, employee_user_id), request_id=get_request_id())


@router.post("/declarations/{employee_user_id}/draft", response_model=ApiResponse[TaxDeclarationRead])
async def hr_save_declaration_route(
    employee_user_id: str,
    payload: TaxDeclarationUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await save_tax_declaration_draft(scope, employee_user_id, payload, self_service=False), request_id=get_request_id())


@router.post("/declarations/{declaration_id}/submit", response_model=ApiResponse[TaxDeclarationRead])
async def hr_submit_declaration_route(declaration_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await submit_tax_declaration(scope, declaration_id, self_service=False), request_id=get_request_id())


@router.post("/declarations/{declaration_id}/review", response_model=ApiResponse[TaxDeclarationRead])
async def review_declaration_route(declaration_id: str, payload: TaxDeclarationReview, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await review_tax_declaration(scope, declaration_id, payload), request_id=get_request_id())


@router.post("/declarations/{declaration_id}/proofs", response_model=ApiResponse[TaxProofRead])
async def add_proof_route(declaration_id: str, payload: TaxProofUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await add_tax_proof(scope, declaration_id, payload, self_service=False), request_id=get_request_id())


@router.post("/proofs/{proof_id}/review", response_model=ApiResponse[TaxProofRead])
async def review_proof_route(proof_id: str, payload: TaxProofReview, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await review_tax_proof(scope, proof_id, payload), request_id=get_request_id())


@router.get("/compliance-report", response_model=ApiResponse[ComplianceReport])
async def compliance_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await compliance_report(scope), request_id=get_request_id())