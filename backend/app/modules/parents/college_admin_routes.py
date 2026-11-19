"""College admin — parent linking and relationship administration."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.ids import to_object_id
from app.modules.auth.models import User
from app.modules.college_admin.deps import college_admin_user
from app.modules.parents.college_review_service import (
    admin_update_relationship,
    list_pending_link_requests,
    review_link_request,
)
from app.modules.parents.enquiry_admin_service import (
    list_academic_enquiries_admin,
    list_attendance_enquiries_admin,
    list_finance_enquiries_admin,
    respond_academic_enquiry,
    respond_attendance_enquiry,
    respond_finance_enquiry,
)
from app.modules.parents.phase2_schemas import ParentEnquiryReview
from app.modules.parents.phase4_schemas import ParentServiceRequestAdminUpdate
from app.modules.parents.meeting_admin_service import decide_meeting_request, list_meeting_requests_admin, record_meeting_outcome
from app.modules.parents.phase5_schemas import ParentMeetingAdminDecision, ParentMeetingOutcomeRecord
from app.modules.parents.service_request_admin_service import list_service_requests_admin, update_service_request_admin
from app.modules.parents.schemas import ParentLinkReviewDecision, ParentLinkRequestRead, ParentRelationshipAdminUpdate

router = APIRouter()


@router.get("/link-requests", response_model=ApiResponse[list[ParentLinkRequestRead]])
async def list_parent_link_requests_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[ParentLinkRequestRead]]:
    return success_response(await list_pending_link_requests(scope), request_id=get_request_id())


@router.post("/link-requests/{request_id}/review", response_model=ApiResponse[dict])
async def review_parent_link_request_route(
    request_id: str,
    payload: ParentLinkReviewDecision,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    admin: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(
        await review_link_request(scope, to_object_id(request_id, "request_id"), payload, reviewer_id=admin.id),
        request_id=get_request_id(),
    )


@router.patch("/relationships/{relationship_id}", response_model=ApiResponse[dict])
async def admin_parent_relationship_route(
    relationship_id: str,
    payload: ParentRelationshipAdminUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    admin: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(
        await admin_update_relationship(
            scope, to_object_id(relationship_id, "relationship_id"), payload, reviewer_id=admin.id
        ),
        request_id=get_request_id(),
    )


@router.get("/attendance-enquiries", response_model=ApiResponse[list[dict]])
async def list_parent_attendance_enquiries_admin_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    status: str | None = None,
) -> ApiResponse[list[dict]]:
    return success_response(await list_attendance_enquiries_admin(scope, status=status), request_id=get_request_id())


@router.post("/attendance-enquiries/{enquiry_id}/respond", response_model=ApiResponse[dict])
async def respond_parent_attendance_enquiry_route(
    enquiry_id: str,
    payload: ParentEnquiryReview,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    admin: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(
        await respond_attendance_enquiry(scope, to_object_id(enquiry_id, "enquiry_id"), payload, reviewer_id=admin.id),
        request_id=get_request_id(),
    )


@router.get("/academic-enquiries", response_model=ApiResponse[list[dict]])
async def list_parent_academic_enquiries_admin_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    status: str | None = None,
) -> ApiResponse[list[dict]]:
    return success_response(await list_academic_enquiries_admin(scope, status=status), request_id=get_request_id())


@router.post("/academic-enquiries/{enquiry_id}/respond", response_model=ApiResponse[dict])
async def respond_parent_academic_enquiry_route(
    enquiry_id: str,
    payload: ParentEnquiryReview,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    admin: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(
        await respond_academic_enquiry(scope, to_object_id(enquiry_id, "enquiry_id"), payload, reviewer_id=admin.id),
        request_id=get_request_id(),
    )


@router.get("/meeting-requests", response_model=ApiResponse[list[dict]])
async def list_parent_meeting_requests_admin_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    status: str | None = None,
) -> ApiResponse[list[dict]]:
    return success_response(await list_meeting_requests_admin(scope, status=status), request_id=get_request_id())


@router.post("/meeting-requests/{request_id}/decide", response_model=ApiResponse[dict])
async def decide_parent_meeting_request_admin_route(
    request_id: str,
    payload: ParentMeetingAdminDecision,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    admin: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(
        await decide_meeting_request(scope, request_id, payload, reviewer_id=admin.id),
        request_id=get_request_id(),
    )


@router.post("/meeting-appointments/{appointment_id}/outcome", response_model=ApiResponse[dict])
async def record_parent_meeting_outcome_admin_route(
    appointment_id: str,
    payload: ParentMeetingOutcomeRecord,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    admin: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(
        await record_meeting_outcome(scope, appointment_id, payload, reviewer_id=admin.id),
        request_id=get_request_id(),
    )


@router.get("/service-requests", response_model=ApiResponse[list[dict]])
async def list_parent_service_requests_admin_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    status: str | None = None,
) -> ApiResponse[list[dict]]:
    return success_response(await list_service_requests_admin(scope, status=status), request_id=get_request_id())


@router.patch("/service-requests/{request_id}", response_model=ApiResponse[dict])
async def update_parent_service_request_admin_route(
    request_id: str,
    payload: ParentServiceRequestAdminUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    admin: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(
        await update_service_request_admin(scope, request_id, payload, reviewer_id=admin.id),
        request_id=get_request_id(),
    )


@router.get("/finance-enquiries", response_model=ApiResponse[list[dict]])
async def list_parent_finance_enquiries_admin_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    status: str | None = None,
) -> ApiResponse[list[dict]]:
    return success_response(await list_finance_enquiries_admin(scope, status=status), request_id=get_request_id())


@router.post("/finance-enquiries/{enquiry_id}/respond", response_model=ApiResponse[dict])
async def respond_parent_finance_enquiry_route(
    enquiry_id: str,
    payload: ParentEnquiryReview,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    admin: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(
        await respond_finance_enquiry(scope, to_object_id(enquiry_id, "enquiry_id"), payload, reviewer_id=admin.id),
        request_id=get_request_id(),
    )