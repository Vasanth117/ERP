"""Examination incidents and malpractice routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_deps import examination_cell_user
from app.modules.examinations.exam_cell_incident_schemas import (
    ExamDisciplinaryDecisionCreate,
    ExamIncidentAssignInvestigator,
    ExamIncidentCreate,
    ExamIncidentEvidenceCreate,
    ExamIncidentRead,
    ExamInvestigationStatement,
    ExamMalpracticeCaseCreate,
    ExamMalpracticeCaseRead,
    ExamMalpracticeFinding,
)
from app.modules.examinations.exam_cell_incident_service import (
    add_incident_evidence,
    assign_investigator,
    get_malpractice_case,
    open_malpractice_case,
    record_disciplinary_decision,
    record_investigation_statement,
    record_malpractice_finding,
    register_incident,
)

router = APIRouter(tags=["examination-cell-incidents"])


@router.post("/incidents", response_model=ApiResponse[ExamIncidentRead])
async def incident_create_route(
    payload: ExamIncidentCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamIncidentRead]:
    return success_response(await register_incident(scope, user, payload), request_id=get_request_id())


@router.post("/malpractice/cases", response_model=ApiResponse[ExamMalpracticeCaseRead])
async def case_open_route(
    payload: ExamMalpracticeCaseCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamMalpracticeCaseRead]:
    return success_response(await open_malpractice_case(scope, user, payload), request_id=get_request_id())


@router.get("/malpractice/cases/{case_id}", response_model=ApiResponse[ExamMalpracticeCaseRead])
async def case_get_route(
    case_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamMalpracticeCaseRead]:
    _ = user
    return success_response(await get_malpractice_case(scope, case_id), request_id=get_request_id())


@router.post("/malpractice/cases/{case_id}/assign-investigator", response_model=ApiResponse[ExamMalpracticeCaseRead])
async def assign_investigator_route(
    case_id: str,
    payload: ExamIncidentAssignInvestigator,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamMalpracticeCaseRead]:
    return success_response(await assign_investigator(scope, user, case_id, payload), request_id=get_request_id())


@router.post("/malpractice/cases/{case_id}/statements", response_model=ApiResponse[dict])
async def statement_route(
    case_id: str,
    payload: ExamInvestigationStatement,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[dict]:
    await record_investigation_statement(scope, user, case_id, payload)
    return success_response({"status": "ok"}, request_id=get_request_id())


@router.post("/malpractice/cases/{case_id}/findings", response_model=ApiResponse[ExamMalpracticeCaseRead])
async def findings_route(
    case_id: str,
    payload: ExamMalpracticeFinding,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamMalpracticeCaseRead]:
    return success_response(await record_malpractice_finding(scope, user, case_id, payload), request_id=get_request_id())


@router.post("/malpractice/cases/{case_id}/disciplinary-decisions", response_model=ApiResponse[dict])
async def decision_route(
    case_id: str,
    payload: ExamDisciplinaryDecisionCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[dict]:
    await record_disciplinary_decision(scope, user, case_id, payload)
    return success_response({"status": "ok"}, request_id=get_request_id())


@router.post("/incidents/{incident_id}/evidence", response_model=ApiResponse[dict])
async def evidence_route(
    incident_id: str,
    payload: ExamIncidentEvidenceCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[dict]:
    await add_incident_evidence(scope, user, incident_id, payload)
    return success_response({"status": "ok"}, request_id=get_request_id())