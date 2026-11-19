"""Finance notifications and reminders API."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.accounts_finance.deps import finance_staff_user
from app.modules.accounts_finance.finance_reminder_service import notification_dashboard, run_fee_due_reminders, upsert_reminder_policy
from app.modules.auth.models import User

router = APIRouter(prefix="/notifications", tags=["accounts-finance-notifications"])


class ReminderPolicyInput(BaseModel):
    category: str
    days_before_due: int = 3
    days_after_due: int = 1
    channel: str = "in_app"
    max_reminders: int = 3
    template_subject: str = "Fee payment reminder"
    template_body: str = "You have an upcoming fee payment of {amount}."


@router.get("/dashboard")
async def notify_dashboard_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await notification_dashboard(scope), request_id=get_request_id())


@router.put("/reminder-policies")
async def reminder_policy_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    body: ReminderPolicyInput,
) -> ApiResponse[dict]:
    return success_response(await upsert_reminder_policy(scope, body.model_dump()), request_id=get_request_id())


@router.post("/reminders/run-fee-due")
async def run_reminders_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await run_fee_due_reminders(scope), request_id=get_request_id())