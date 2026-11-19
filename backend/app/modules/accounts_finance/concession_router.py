"""Phase 5 fee concession and waiver routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.accounts_finance.concession_service import (
    approve_concession_application,
    approve_waiver,
    list_categories,
    list_concession_applications,
    reject_concession_application,
    revoke_concession_award,
    upsert_category,
    upsert_policy,
    submit_concession_application,
)
from app.modules.accounts_finance.deps import finance_staff_user
from app.modules.auth.models import User


class CategoryInput(BaseModel):
    category_id: str | None = None
    code: str
    name: str
    description: str | None = None
    active: bool = True


class PolicyInput(BaseModel):
    policy_id: str | None = None
    policy_code: str
    name: str
    description: str | None = None
    category_id: str | None = None
    applicable_programmes: list[str] = Field(default_factory=list)
    applicable_fee_categories: list[str] = Field(default_factory=list)
    concession_type: str = "fixed"
    fixed_amount: float | None = Field(default=None, ge=0)
    percent_amount: float | None = Field(default=None, ge=0, le=100)
    max_limit: float | None = Field(default=None, ge=0)
    academic_year_label: str | None = None
    stacking_rules: dict[str, Any] = Field(default_factory=dict)
    active: bool = True


class ConcessionApplicationInput(BaseModel):
    student_user_id: str
    policy_id: str
    reason: str = Field(min_length=3)
    requested_amount: float | None = Field(default=None, ge=0)
    requested_percent: float | None = Field(default=None, ge=0, le=100)
    assessment_id: str | None = None
    invoice_id: str | None = None
    academic_year_label: str | None = None
    semester_label: str | None = None
    document_refs: list[str] = Field(default_factory=list)


class ConcessionApproveInput(BaseModel):
    approved_amount: float | None = Field(default=None, ge=0)


class WaiverInput(BaseModel):
    student_user_id: str
    original_amount: float = Field(ge=0)
    waived_amount: float = Field(ge=0)
    reason: str = Field(min_length=3)
    waiver_type: str = "partial"
    invoice_id: str | None = None
    assessment_id: str | None = None
    policy_id: str | None = None
    academic_year_label: str | None = None
    semester_label: str | None = None
    document_refs: list[str] = Field(default_factory=list)


router = APIRouter(prefix="/concessions", tags=["accounts-finance-concessions"])


@router.get("/categories", response_model=ApiResponse[list])
async def categories_list(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[list]:
    return success_response(await list_categories(scope), request_id=get_request_id())


@router.post("/categories", response_model=ApiResponse[dict])
async def categories_upsert(
    payload: CategoryInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await upsert_category(scope, payload.model_dump()), request_id=get_request_id())


@router.post("/policies", response_model=ApiResponse[dict])
async def policies_upsert(
    payload: PolicyInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await upsert_policy(scope, payload.model_dump()), request_id=get_request_id())


@router.get("/applications", response_model=ApiResponse[Page[dict]])
async def applications_list(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    student_user_id: str | None = None,
) -> ApiResponse[Page[dict]]:
    return success_response(await list_concession_applications(scope, pagination, student_user_id), request_id=get_request_id())


@router.post("/applications", response_model=ApiResponse[dict])
async def applications_submit(
    payload: ConcessionApplicationInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await submit_concession_application(scope, payload.model_dump()), request_id=get_request_id())


@router.post("/applications/{application_id}/approve", response_model=ApiResponse[dict])
async def applications_approve(
    application_id: str,
    payload: ConcessionApproveInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(
        await approve_concession_application(scope, application_id, approved_amount=payload.approved_amount),
        request_id=get_request_id(),
    )


@router.post("/applications/{application_id}/reject", response_model=ApiResponse[dict])
async def applications_reject(
    application_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
    reason: Annotated[str, Query(min_length=3)],
) -> ApiResponse[dict]:
    return success_response(await reject_concession_application(scope, application_id, reason), request_id=get_request_id())


@router.post("/waivers", response_model=ApiResponse[dict])
async def waivers_approve(
    payload: WaiverInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await approve_waiver(scope, payload.model_dump()), request_id=get_request_id())


@router.post("/awards/{award_id}/revoke", response_model=ApiResponse[dict])
async def awards_revoke(
    award_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
    reason: Annotated[str, Query(min_length=3)],
) -> ApiResponse[dict]:
    return success_response(await revoke_concession_award(scope, award_id, reason), request_id=get_request_id())