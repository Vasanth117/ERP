"""HR employee document routes."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.hr.deps import hr_staff_user
from app.modules.hr.document_schemas import (
    DocumentEventRead,
    DocumentUploadMeta,
    DocumentVerificationDecision,
    EmployeeDocumentOverview,
    EmployeeDocumentRead,
    ExpiryPolicyUpsert,
    HrDocumentCategoryRead,
    MandatoryDocumentStatus,
    MandatoryRuleUpsert,
)
from app.modules.hr.document_service import (
    document_history,
    download_employee_document,
    employee_document_overview,
    list_document_categories,
    list_employee_documents,
    mandatory_status_for_employee,
    submit_document,
    upload_employee_document,
    upsert_expiry_policy,
    upsert_mandatory_rule,
    verify_document,
)

router = APIRouter(prefix="/documents", tags=["hr-documents"])


@router.get("/categories", response_model=ApiResponse[list[HrDocumentCategoryRead]])
async def document_categories_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await list_document_categories(scope), request_id=get_request_id())


@router.put("/mandatory-rules", response_model=ApiResponse[dict])
async def mandatory_rule_route(payload: MandatoryRuleUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await upsert_mandatory_rule(scope, payload), request_id=get_request_id())


@router.put("/expiry-policy", response_model=ApiResponse[dict])
async def expiry_policy_route(payload: ExpiryPolicyUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await upsert_expiry_policy(scope, payload), request_id=get_request_id())


@router.post("/upload", response_model=ApiResponse[EmployeeDocumentRead])
async def upload_document_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(hr_staff_user)],
    employee_user_id: Annotated[str, Form()],
    category_code: Annotated[str, Form()],
    title: Annotated[str, Form()],
    document_code: Annotated[str | None, Form()] = None,
    issue_date: Annotated[date | None, Form()] = None,
    expires_on: Annotated[date | None, Form()] = None,
    issuing_authority: Annotated[str | None, Form()] = None,
    remarks: Annotated[str | None, Form()] = None,
    replace_document_id: Annotated[str | None, Form()] = None,
    submit_for_verification: Annotated[bool, Form()] = True,
    file: UploadFile = File(...),
):
    meta = DocumentUploadMeta(
        employee_user_id=employee_user_id,
        category_code=category_code,
        document_code=document_code,
        title=title,
        issue_date=issue_date,
        expires_on=expires_on,
        issuing_authority=issuing_authority,
        remarks=remarks,
        replace_document_id=replace_document_id,
        submit_for_verification=submit_for_verification,
    )
    return success_response(await upload_employee_document(scope, user, meta, file), request_id=get_request_id())


@router.post("/{document_id}/submit", response_model=ApiResponse[EmployeeDocumentRead])
async def submit_document_route(document_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await submit_document(scope, document_id), request_id=get_request_id())


@router.post("/{document_id}/verification", response_model=ApiResponse[EmployeeDocumentRead])
async def verify_document_route(
    document_id: str,
    payload: DocumentVerificationDecision,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await verify_document(scope, document_id, payload), request_id=get_request_id())


@router.get("/employees/{employee_user_id}", response_model=ApiResponse[Page[EmployeeDocumentRead]])
async def list_documents_route(
    employee_user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
):
    return success_response(await list_employee_documents(scope, employee_user_id, pagination), request_id=get_request_id())


@router.get("/employees/{employee_user_id}/overview", response_model=ApiResponse[EmployeeDocumentOverview])
async def document_overview_route(employee_user_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await employee_document_overview(scope, employee_user_id), request_id=get_request_id())


@router.get("/employees/{employee_user_id}/mandatory", response_model=ApiResponse[list[MandatoryDocumentStatus]])
async def mandatory_documents_route(employee_user_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await mandatory_status_for_employee(scope, employee_user_id), request_id=get_request_id())


@router.get("/{document_id}/history", response_model=ApiResponse[list[DocumentEventRead]])
async def document_history_route(document_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await document_history(scope, document_id), request_id=get_request_id())


@router.get("/{document_id}/download")
async def download_document_route(
    document_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(hr_staff_user)],
):
    data, mime, filename = await download_employee_document(scope, document_id, user)
    return Response(content=data, media_type=mime, headers={"Content-Disposition": f'attachment; filename="{filename}"'})