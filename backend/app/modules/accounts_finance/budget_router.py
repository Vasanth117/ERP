"""Finance budget REST API."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.accounts_finance.budget_service import (
    add_budget_line,
    allocate_budget,
    approve_budget,
    approve_budget_revision,
    budget_overview,
    budget_utilization,
    create_budget,
    record_commitment,
    request_budget_revision,
    submit_budget,
)
from app.modules.accounts_finance.deps import finance_staff_user
from app.modules.auth.models import User

router = APIRouter(prefix="/budgets", tags=["accounts-finance-budgets"])


class BudgetInput(BaseModel):
    budget_code: str
    budget_name: str
    financial_year_id: str
    total_amount: float = Field(gt=0)
    budget_category: str | None = None
    department_id: str | None = None
    campus_id: str | None = None
    cost_centre_code: str | None = None
    owner_id: str | None = None
    justification: str | None = None


class BudgetLineInput(BaseModel):
    category: str
    amount: float = Field(gt=0)
    period_code: str | None = None
    note: str | None = None


class AllocationInput(BaseModel):
    allocated_amount: float = Field(gt=0)
    department_id: str | None = None
    cost_centre_code: str | None = None
    project_code: str | None = None
    period_code: str | None = None


class CommitmentInput(BaseModel):
    reference_type: str
    reference_id: str
    amount: float = Field(gt=0)
    allocation_id: str | None = None
    note: str | None = None


class RevisionInput(BaseModel):
    revised_amount: float = Field(gt=0)
    reason: str = Field(min_length=5)


@router.get("/overview")
async def budget_overview_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(finance_staff_user)]) -> ApiResponse[dict]:
    return success_response(await budget_overview(scope), request_id=get_request_id())


@router.post("")
async def create_budget_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    body: BudgetInput,
) -> ApiResponse[dict]:
    return success_response(await create_budget(scope, body.model_dump()), request_id=get_request_id())


@router.post("/{budget_id}/lines")
async def add_line_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    budget_id: str,
    body: BudgetLineInput,
) -> ApiResponse[dict]:
    return success_response(await add_budget_line(scope, budget_id, body.model_dump()), request_id=get_request_id())


@router.post("/{budget_id}/submit")
async def submit_budget_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    budget_id: str,
) -> ApiResponse[dict]:
    return success_response(await submit_budget(scope, budget_id), request_id=get_request_id())


@router.post("/{budget_id}/approve")
async def approve_budget_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    budget_id: str,
) -> ApiResponse[dict]:
    return success_response(await approve_budget(scope, budget_id), request_id=get_request_id())


@router.post("/{budget_id}/allocations")
async def allocate_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    budget_id: str,
    body: AllocationInput,
) -> ApiResponse[dict]:
    return success_response(await allocate_budget(scope, budget_id, body.model_dump()), request_id=get_request_id())


@router.post("/{budget_id}/commitments")
async def commitment_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    budget_id: str,
    body: CommitmentInput,
) -> ApiResponse[dict]:
    return success_response(await record_commitment(scope, budget_id, body.model_dump()), request_id=get_request_id())


@router.get("/{budget_id}/utilization")
async def utilization_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    budget_id: str,
) -> ApiResponse[dict]:
    return success_response(await budget_utilization(scope, budget_id), request_id=get_request_id())


@router.post("/{budget_id}/revisions")
async def revision_request_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    budget_id: str,
    body: RevisionInput,
) -> ApiResponse[dict]:
    return success_response(await request_budget_revision(scope, budget_id, body.revised_amount, body.reason), request_id=get_request_id())


@router.post("/revisions/{revision_id}/approve")
async def approve_revision_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    revision_id: str,
) -> ApiResponse[dict]:
    return success_response(await approve_budget_revision(scope, revision_id), request_id=get_request_id())