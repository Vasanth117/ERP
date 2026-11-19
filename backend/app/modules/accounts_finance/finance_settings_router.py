"""Finance settings and access management API."""

from datetime import date, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.accounts_finance.deps import finance_staff_user
from app.modules.accounts_finance.finance_access_service import (
    assign_finance_scope,
    grant_temporary_access,
    list_active_access,
    revoke_assignment,
)
from app.modules.accounts_finance.finance_settings_service import (
    activate_settings_version,
    approve_settings_version,
    create_settings_draft,
    create_workflow_version,
    get_active_settings,
    list_finance_roles,
    settings_dashboard,
    submit_settings_version,
    upsert_approval_workflow,
)
from app.modules.auth.models import User

router = APIRouter(prefix="/settings", tags=["accounts-finance-settings"])


class SettingsDraftInput(BaseModel):
    domain: str
    payload: dict[str, Any] = Field(default_factory=dict)


class WorkflowInput(BaseModel):
    workflow_key: str
    label: str
    transaction_category: str


class WorkflowVersionInput(BaseModel):
    stages: list[dict[str, Any]]
    rules: dict[str, Any] | None = None


class AccessAssignInput(BaseModel):
    user_id: str
    scope_type: str
    scope_ref: str | None = None


class TempGrantInput(BaseModel):
    user_id: str
    permissions: list[str] = Field(default_factory=list)
    valid_to: datetime


@router.get("/dashboard")
async def settings_dashboard_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(finance_staff_user)]) -> ApiResponse[dict]:
    return success_response(await settings_dashboard(scope), request_id=get_request_id())


@router.get("/domains/{domain}/active")
async def active_settings_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(finance_staff_user)], domain: str) -> ApiResponse[dict]:
    return success_response(await get_active_settings(scope, domain), request_id=get_request_id())


@router.post("/versions")
async def create_settings_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(finance_staff_user)], body: SettingsDraftInput) -> ApiResponse[dict]:
    return success_response(await create_settings_draft(scope, body.domain, body.payload), request_id=get_request_id())


@router.post("/versions/{domain}/{version_id}/submit")
async def submit_settings_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    domain: str,
    version_id: str,
) -> ApiResponse[dict]:
    return success_response(await submit_settings_version(scope, domain, version_id), request_id=get_request_id())


@router.post("/versions/{domain}/{version_id}/approve")
async def approve_settings_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    domain: str,
    version_id: str,
) -> ApiResponse[dict]:
    return success_response(await approve_settings_version(scope, domain, version_id), request_id=get_request_id())


@router.post("/versions/{domain}/{version_id}/activate")
async def activate_settings_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    domain: str,
    version_id: str,
    effective_from: date | None = None,
) -> ApiResponse[dict]:
    return success_response(await activate_settings_version(scope, domain, version_id, effective_from=effective_from), request_id=get_request_id())


@router.get("/roles")
async def finance_roles_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(finance_staff_user)]) -> ApiResponse[dict]:
    return success_response(await list_finance_roles(scope), request_id=get_request_id())


@router.put("/workflows")
async def workflow_upsert_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    body: WorkflowInput,
) -> ApiResponse[dict]:
    return success_response(await upsert_approval_workflow(scope, body.workflow_key, body.label, body.transaction_category), request_id=get_request_id())


@router.post("/workflows/{workflow_key}/versions")
async def workflow_version_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    workflow_key: str,
    body: WorkflowVersionInput,
) -> ApiResponse[dict]:
    return success_response(await create_workflow_version(scope, workflow_key, body.stages, body.rules), request_id=get_request_id())


@router.post("/access/assignments")
async def assign_access_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    body: AccessAssignInput,
) -> ApiResponse[dict]:
    return success_response(await assign_finance_scope(scope, body.model_dump()), request_id=get_request_id())


@router.get("/access")
async def list_access_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    user_id: str | None = None,
) -> ApiResponse[dict]:
    return success_response(await list_active_access(scope, user_id), request_id=get_request_id())


@router.post("/access/temporary-grants")
async def temp_grant_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    body: TempGrantInput,
) -> ApiResponse[dict]:
    return success_response(await grant_temporary_access(scope, body.model_dump()), request_id=get_request_id())


@router.post("/access/assignments/{assignment_id}/revoke")
async def revoke_access_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    assignment_id: str,
) -> ApiResponse[dict]:
    return success_response(await revoke_assignment(scope, assignment_id), request_id=get_request_id())