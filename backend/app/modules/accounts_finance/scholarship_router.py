"""Phase 5 scholarship routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.accounts_finance.deps import finance_staff_user
from app.modules.accounts_finance.financial_aid_statement_service import student_financial_aid_statement
from app.modules.accounts_finance.scholarship_service import (
    approve_application,
    decide_renewal,
    evaluate_student_eligibility,
    funding_summary,
    list_applications,
    list_programs,
    record_staff_award,
    reject_application,
    review_application,
    submit_renewal,
    upsert_eligibility_rule,
    upsert_funding,
    upsert_program,
)
from app.modules.auth.models import User


class ScholarshipProgramInput(BaseModel):
    programme_id: str | None = None
    scholarship_code: str | None = None
    title: str
    description: str | None = None
    funding_source: str | None = None
    scholarship_type: str | None = None
    academic_year_label: str | None = None
    applicable_programmes: list[str] = Field(default_factory=list)
    applicable_departments: list[str] = Field(default_factory=list)
    eligible_student_categories: list[str] = Field(default_factory=list)
    eligibility_conditions: dict[str, Any] = Field(default_factory=dict)
    max_award_amount: float | None = Field(default=None, ge=0)
    award_calculation_method: str | None = None
    fund_budget_reference: str | None = None
    max_awards: int | None = Field(default=None, ge=0)
    application_start: str | None = None
    application_deadline: str | None = None
    approval_requirements: list[str] = Field(default_factory=list)
    renewal_rules: dict[str, Any] = Field(default_factory=dict)
    program_status: str = "draft"
    applications_open: bool = False


class EligibilityRuleInput(BaseModel):
    rule_id: str | None = None
    rule_name: str
    field_path: str
    operator: str
    value: Any = None
    required: bool = True
    active: bool = True


class ReviewInput(BaseModel):
    recommendation: str
    comments: str | None = None


class ApproveApplicationInput(BaseModel):
    approved_amount: float = Field(gt=0)
    invoice_id: str | None = None
    allow_over_budget: bool = False


class StaffAwardInput(BaseModel):
    student_user_id: str
    programme_id: str
    approved_amount: float = Field(gt=0)
    funding_source: str | None = None
    invoice_id: str | None = None
    academic_year_label: str | None = None
    semester_label: str | None = None


class FundingInput(BaseModel):
    funding_source: str
    total_fund: float = Field(ge=0)


class RenewalDecideInput(BaseModel):
    approved: bool
    approved_amount: float | None = Field(default=None, ge=0)


router = APIRouter(prefix="/scholarships", tags=["accounts-finance-scholarships"])


@router.get("/programs", response_model=ApiResponse[Page[dict]])
async def programs_list(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[dict]]:
    return success_response(await list_programs(scope, pagination), request_id=get_request_id())


@router.post("/programs", response_model=ApiResponse[dict])
async def programs_upsert(
    payload: ScholarshipProgramInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await upsert_program(scope, payload.model_dump()), request_id=get_request_id())


@router.post("/programs/{programme_id}/rules", response_model=ApiResponse[dict])
async def rules_upsert(
    programme_id: str,
    payload: EligibilityRuleInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(
        await upsert_eligibility_rule(scope, programme_id, payload.model_dump()),
        request_id=get_request_id(),
    )


@router.get("/programs/{programme_id}/eligibility", response_model=ApiResponse[dict])
async def eligibility_check(
    programme_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
    student_user_id: Annotated[str, Query()],
) -> ApiResponse[dict]:
    return success_response(
        await evaluate_student_eligibility(scope, programme_id, student_user_id),
        request_id=get_request_id(),
    )


@router.get("/applications", response_model=ApiResponse[Page[dict]])
async def applications_list(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    programme_id: str | None = None,
) -> ApiResponse[Page[dict]]:
    return success_response(await list_applications(scope, pagination, programme_id), request_id=get_request_id())


@router.post("/applications/{application_id}/review", response_model=ApiResponse[dict])
async def application_review(
    application_id: str,
    payload: ReviewInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(
        await review_application(scope, application_id, payload.recommendation, payload.comments),
        request_id=get_request_id(),
    )


@router.post("/applications/{application_id}/approve", response_model=ApiResponse[dict])
async def application_approve(
    application_id: str,
    payload: ApproveApplicationInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(
        await approve_application(
            scope,
            application_id,
            approved_amount=payload.approved_amount,
            invoice_id=payload.invoice_id,
            allow_over_budget=payload.allow_over_budget,
        ),
        request_id=get_request_id(),
    )


@router.post("/applications/{application_id}/reject", response_model=ApiResponse[dict])
async def application_reject(
    application_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
    reason: Annotated[str, Query(min_length=3)],
) -> ApiResponse[dict]:
    return success_response(await reject_application(scope, application_id, reason), request_id=get_request_id())


@router.post("/awards/staff-recorded", response_model=ApiResponse[dict])
async def staff_award(
    payload: StaffAwardInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await record_staff_award(scope, payload.model_dump()), request_id=get_request_id())


@router.post("/programs/{programme_id}/funding", response_model=ApiResponse[dict])
async def funding_upsert(
    programme_id: str,
    payload: FundingInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(
        await upsert_funding(scope, programme_id, payload.funding_source, payload.total_fund),
        request_id=get_request_id(),
    )


@router.get("/programs/{programme_id}/funding", response_model=ApiResponse[list])
async def funding_get(
    programme_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[list]:
    return success_response(await funding_summary(scope, programme_id), request_id=get_request_id())


@router.post("/awards/{award_id}/renewals", response_model=ApiResponse[dict])
async def renewal_submit(
    award_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
    academic_year_label: Annotated[str, Query()],
) -> ApiResponse[dict]:
    return success_response(await submit_renewal(scope, award_id, academic_year_label), request_id=get_request_id())


@router.post("/renewals/{renewal_id}/decide", response_model=ApiResponse[dict])
async def renewal_decide(
    renewal_id: str,
    payload: RenewalDecideInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(
        await decide_renewal(scope, renewal_id, approved=payload.approved, approved_amount=payload.approved_amount),
        request_id=get_request_id(),
    )


@router.get("/students/{student_user_id}/aid-statement", response_model=ApiResponse[dict])
async def aid_statement(
    student_user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
    invoice_id: str | None = None,
) -> ApiResponse[dict]:
    return success_response(
        await student_financial_aid_statement(scope, student_user_id, invoice_id),
        request_id=get_request_id(),
    )