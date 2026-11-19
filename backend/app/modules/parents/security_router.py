"""Parent account security routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.parents.deps import parent_user
from app.modules.parents.phase5_schemas import (
    ParentContactChangeRequestCreate,
    ParentRelationshipReviewCreate,
    ParentSecurityAccountRead,
    ParentSecuritySessionRead,
)
from app.modules.parents.security_portal_service import (
    get_security_account,
    list_sessions,
    login_activity,
    request_contact_change,
    revoke_other_sessions,
    submit_relationship_review,
)

router = APIRouter()


@router.get("/account", response_model=ApiResponse[ParentSecurityAccountRead])
async def parent_security_account_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ParentSecurityAccountRead]:
    return success_response(await get_security_account(scope, user), request_id=get_request_id())


@router.get("/sessions", response_model=ApiResponse[list[ParentSecuritySessionRead]])
async def parent_security_sessions_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[ParentSecuritySessionRead]]:
    return success_response(await list_sessions(scope, user), request_id=get_request_id())


@router.post("/sessions/revoke-all", response_model=ApiResponse[dict])
async def parent_security_revoke_sessions_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[dict]:
    return success_response(await revoke_other_sessions(scope, user), request_id=get_request_id())


@router.get("/login-activity", response_model=ApiResponse[list[dict]])
async def parent_security_login_activity_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[dict]]:
    return success_response(await login_activity(scope, user), request_id=get_request_id())


@router.post("/contact-change-requests", response_model=ApiResponse[dict])
async def parent_contact_change_request_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    payload: ParentContactChangeRequestCreate,
) -> ApiResponse[dict]:
    return success_response(await request_contact_change(scope, user, payload), request_id=get_request_id())


@router.post("/relationships/{relationship_id}/review-requests", response_model=ApiResponse[dict])
async def parent_relationship_review_route(
    relationship_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    payload: ParentRelationshipReviewCreate,
) -> ApiResponse[dict]:
    return success_response(
        await submit_relationship_review(scope, user, relationship_id, payload),
        request_id=get_request_id(),
    )