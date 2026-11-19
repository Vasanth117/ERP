"""Hostel rules and incident routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.hostel.deps import hostel_admin_user
from app.modules.hostel.rules_incident_models import HostelIncidentStatus
from app.modules.hostel.rules_incident_schemas import (
    DisciplinaryActionInput,
    HostelRuleRead,
    HostelRuleUpsertPortal,
    IncidentEvidenceInput,
    IncidentInvestigationUpdate,
    IncidentOverview,
    IncidentRead,
    IncidentReportInput,
    IncidentStatusUpdate,
    RulePublishInput,
)
from app.modules.hostel.rules_incident_service import (
    add_incident_evidence,
    get_incident,
    incident_overview,
    list_incidents,
    list_published_rules,
    publish_rule,
    record_disciplinary_action,
    report_incident,
    update_incident_status,
    update_investigation,
    upsert_rule,
)

router = APIRouter(prefix="/me", tags=["hostel-rules-incidents"])


@router.put("/rules", response_model=ApiResponse[HostelRuleRead])
async def rule_upsert_route(
    payload: HostelRuleUpsertPortal,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await upsert_rule(scope, payload), request_id=get_request_id())


@router.post("/rules/publish", response_model=ApiResponse[HostelRuleRead])
async def rule_publish_route(
    payload: RulePublishInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await publish_rule(scope, payload), request_id=get_request_id())


@router.get("/rules/published", response_model=ApiResponse[list[HostelRuleRead]])
async def rules_published_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    hostel_code: Annotated[str | None, Query()] = None,
):
    return success_response(await list_published_rules(scope, hostel_code=hostel_code), request_id=get_request_id())


@router.get("/incidents/overview", response_model=ApiResponse[IncidentOverview])
async def incident_overview_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await incident_overview(scope), request_id=get_request_id())


@router.post("/incidents", response_model=ApiResponse[IncidentRead], status_code=status.HTTP_201_CREATED)
async def incident_report_route(
    payload: IncidentReportInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await report_incident(scope, payload), request_id=get_request_id())


@router.get("/incidents", response_model=ApiResponse[Page[IncidentRead]])
async def incident_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    status: Annotated[HostelIncidentStatus | None, Query()] = None,
):
    return success_response(await list_incidents(scope, pagination, status=status), request_id=get_request_id())


@router.get("/incidents/{incident_id}", response_model=ApiResponse[IncidentRead])
async def incident_get_route(
    incident_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await get_incident(scope, incident_id), request_id=get_request_id())


@router.post("/incidents/status", response_model=ApiResponse[IncidentRead])
async def incident_status_route(
    payload: IncidentStatusUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await update_incident_status(scope, payload), request_id=get_request_id())


@router.post("/incidents/investigation", response_model=ApiResponse[dict])
async def incident_investigation_route(
    payload: IncidentInvestigationUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await update_investigation(scope, payload), request_id=get_request_id())


@router.post("/incidents/evidence", response_model=ApiResponse[dict])
async def incident_evidence_route(
    payload: IncidentEvidenceInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await add_incident_evidence(scope, payload), request_id=get_request_id())


@router.post("/incidents/disciplinary", response_model=ApiResponse[dict])
async def disciplinary_route(
    payload: DisciplinaryActionInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await record_disciplinary_action(scope, payload), request_id=get_request_id())