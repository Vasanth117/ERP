"""HR salary structure routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.hr.deps import hr_staff_user
from app.api.deps import get_access_scope
from app.modules.hr.salary_structure_schemas import (
    SalaryAssignmentCreate,
    SalaryAssignmentRead,
    SalaryComponentRead,
    SalaryComponentUpsert,
    SalaryRevisionCreate,
    SalaryRevisionRead,
    SalaryRevisionReview,
    SalaryTemplateRead,
    SalaryTemplateUpsert,
)
from app.modules.hr.salary_structure_service import (
    activate_salary_assignment,
    create_salary_assignment,
    create_salary_revision,
    list_salary_components,
    list_salary_templates,
    review_salary_revision,
    submit_salary_assignment,
    upsert_salary_component,
    upsert_salary_template,
)

router = APIRouter(prefix="/salary", tags=["hr-salary"])


@router.put("/components", response_model=ApiResponse[SalaryComponentRead])
async def component_upsert_route(payload: SalaryComponentUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await upsert_salary_component(scope, payload), request_id=get_request_id())


@router.get("/components", response_model=ApiResponse[list[SalaryComponentRead]])
async def list_components_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await list_salary_components(scope), request_id=get_request_id())


@router.put("/templates", response_model=ApiResponse[SalaryTemplateRead])
async def template_upsert_route(
    payload: SalaryTemplateUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    duplicate: Annotated[bool, Query()] = False,
):
    return success_response(await upsert_salary_template(scope, payload, duplicate=duplicate), request_id=get_request_id())


@router.get("/templates", response_model=ApiResponse[list[SalaryTemplateRead]])
async def list_templates_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await list_salary_templates(scope), request_id=get_request_id())


@router.post("/assignments", response_model=ApiResponse[SalaryAssignmentRead])
async def create_assignment_route(payload: SalaryAssignmentCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await create_salary_assignment(scope, payload), request_id=get_request_id())


@router.post("/assignments/{assignment_id}/submit", response_model=ApiResponse[SalaryAssignmentRead])
async def submit_assignment_route(assignment_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await submit_salary_assignment(scope, assignment_id), request_id=get_request_id())


@router.post("/assignments/{assignment_id}/activate", response_model=ApiResponse[SalaryAssignmentRead])
async def activate_assignment_route(assignment_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await activate_salary_assignment(scope, assignment_id), request_id=get_request_id())


@router.post("/revisions", response_model=ApiResponse[SalaryRevisionRead])
async def create_revision_route(payload: SalaryRevisionCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await create_salary_revision(scope, payload), request_id=get_request_id())


@router.post("/revisions/{revision_id}/review", response_model=ApiResponse[SalaryRevisionRead])
async def review_revision_route(
    revision_id: str,
    payload: SalaryRevisionReview,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await review_salary_revision(scope, revision_id, payload), request_id=get_request_id())