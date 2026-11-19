"""HR settings and policy routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.hr.deps import hr_staff_user
from app.modules.hr.hr_settings_schemas import (
    GeneralSettingsRead,
    GeneralSettingsUpsert,
    PolicyAcknowledgeRequest,
    PolicyAcknowledgementRead,
    PolicyApprovalRead,
    PolicyCategoryRead,
    PolicyCategoryUpsert,
    PolicyRead,
    PolicyTransition,
    PolicyUpsert,
    PolicyVersionRead,
)
from app.modules.hr.hr_settings_service import (
    acknowledge_policy,
    get_general_settings,
    get_policy,
    list_pending_acknowledgements,
    list_policies,
    list_policy_acknowledgements,
    list_policy_approvals,
    list_policy_categories,
    list_policy_versions,
    send_acknowledgement_reminders,
    transition_policy,
    upsert_general_settings,
    upsert_policy,
    upsert_policy_category,
)

router = APIRouter(prefix="/settings", tags=["hr-settings"])


@router.get("/general", response_model=ApiResponse[GeneralSettingsRead])
async def general_get(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await get_general_settings(scope), request_id=get_request_id())


@router.put("/general", response_model=ApiResponse[GeneralSettingsRead])
async def general_put(payload: GeneralSettingsUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await upsert_general_settings(scope, payload), request_id=get_request_id())


@router.get("/policy-categories", response_model=ApiResponse[list[PolicyCategoryRead]])
async def categories_list(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await list_policy_categories(scope), request_id=get_request_id())


@router.put("/policy-categories", response_model=ApiResponse[PolicyCategoryRead])
async def categories_put(payload: PolicyCategoryUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await upsert_policy_category(scope, payload), request_id=get_request_id())


@router.get("/policies", response_model=ApiResponse[list[PolicyRead]])
async def policies_list(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    category_code: str | None = Query(default=None),
):
    return success_response(await list_policies(scope, category_code), request_id=get_request_id())


@router.put("/policies", response_model=ApiResponse[PolicyRead])
async def policies_put(payload: PolicyUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await upsert_policy(scope, payload), request_id=get_request_id())


@router.get("/policies/{policy_id}", response_model=ApiResponse[PolicyRead])
async def policy_get(policy_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await get_policy(scope, policy_id), request_id=get_request_id())


@router.post("/policies/{policy_id}/transition", response_model=ApiResponse[PolicyRead])
async def policy_transition(
    policy_id: str,
    payload: PolicyTransition,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await transition_policy(scope, policy_id, payload), request_id=get_request_id())


@router.get("/policies/{policy_id}/versions", response_model=ApiResponse[list[PolicyVersionRead]])
async def policy_versions(policy_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await list_policy_versions(scope, policy_id), request_id=get_request_id())


@router.get("/policies/{policy_id}/approvals", response_model=ApiResponse[list[PolicyApprovalRead]])
async def policy_approvals(policy_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await list_policy_approvals(scope, policy_id), request_id=get_request_id())


@router.get("/acknowledgements/pending", response_model=ApiResponse[list[PolicyAcknowledgementRead]])
async def ack_pending(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    employee_user_id: str | None = Query(default=None),
):
    return success_response(await list_pending_acknowledgements(scope, employee_user_id), request_id=get_request_id())


@router.get("/policies/{policy_id}/acknowledgements", response_model=ApiResponse[list[PolicyAcknowledgementRead]])
async def ack_list_policy(policy_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await list_policy_acknowledgements(scope, policy_id), request_id=get_request_id())


@router.post("/acknowledgements/remind", response_model=ApiResponse[dict])
async def ack_remind(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    policy_id: str | None = Query(default=None),
):
    return success_response(await send_acknowledgement_reminders(scope, policy_id), request_id=get_request_id())


@router.post("/policies/{policy_id}/acknowledge", response_model=ApiResponse[PolicyAcknowledgementRead])
async def ack_policy(
    policy_id: str,
    payload: PolicyAcknowledgeRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await acknowledge_policy(scope, policy_id, payload), request_id=get_request_id())