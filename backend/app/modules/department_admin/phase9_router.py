"""Department Admin phase 9 — documents and security audit history."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.department_admin.audit_history_service import (
    approval_audit_history,
    audit_summary,
    configuration_change_history,
    effective_department_permissions,
    export_department_audit,
    get_department_audit_event,
    list_department_audit,
    list_department_security_events,
)
from app.modules.department_admin.deps import department_admin_user
from app.modules.department_admin.document_service import (
    archive_document,
    create_document_version,
    document_history,
    download_document,
    get_document,
    list_document_categories,
    list_document_versions,
    list_documents,
    update_document,
    upload_document,
)
from app.modules.department_admin.models import DepartmentDocumentAccessScope, DepartmentDocumentStatus
from app.modules.department_admin.phase9_schemas import (
    AuditExportBody,
    AuditExportRead,
    AuditListFilters,
    AuditSummaryRead,
    ConfigurationChangeRead,
    DepartmentAuditRead,
    DocumentArchiveBody,
    DocumentDownloadRead,
    DocumentHistoryRead,
    DocumentListFilters,
    DocumentRead,
    DocumentUpdateBody,
    DocumentUploadBody,
    DocumentVersionBody,
    DocumentVersionRead,
    EffectivePermissionsRead,
    SecurityEventDeptRead,
)

phase9_router = APIRouter()


def _document_filters(
    q: Annotated[str | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
    status: Annotated[DepartmentDocumentStatus | None, Query()] = None,
    access_scope: Annotated[DepartmentDocumentAccessScope | None, Query()] = None,
    academic_year_label: Annotated[str | None, Query()] = None,
    programme_code: Annotated[str | None, Query()] = None,
    uploaded_by: Annotated[str | None, Query()] = None,
    tag: Annotated[str | None, Query()] = None,
    date_from: Annotated[datetime | None, Query()] = None,
    date_to: Annotated[datetime | None, Query()] = None,
) -> DocumentListFilters:
    return DocumentListFilters(
        q=q,
        category=category,
        status=status,
        access_scope=access_scope,
        academic_year_label=academic_year_label,
        programme_code=programme_code,
        uploaded_by=uploaded_by,
        tag=tag,
        date_from=date_from,
        date_to=date_to,
    )


def _audit_filters(
    date_from: Annotated[datetime | None, Query()] = None,
    date_to: Annotated[datetime | None, Query()] = None,
    actor_id: Annotated[str | None, Query()] = None,
    action_category: Annotated[str | None, Query()] = None,
    action: Annotated[str | None, Query()] = None,
    resource_type: Annotated[str | None, Query()] = None,
    outcome: Annotated[str | None, Query()] = None,
    resource_id: Annotated[str | None, Query()] = None,
) -> AuditListFilters:
    return AuditListFilters(
        date_from=date_from,
        date_to=date_to,
        actor_id=actor_id,
        action_category=action_category,
        action=action,
        resource_type=resource_type,
        outcome=outcome,
        resource_id=resource_id,
    )


@phase9_router.get("/documents/categories", response_model=ApiResponse[list[str]])
async def department_document_categories_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[list[str]]:
    return success_response(list_document_categories(scope), request_id=get_request_id())


@phase9_router.get("/documents", response_model=ApiResponse[Page[DocumentRead]])
async def department_documents_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    filters: Annotated[DocumentListFilters, Depends(_document_filters)],
) -> ApiResponse[Page[DocumentRead]]:
    data = await list_documents(scope, user, pagination, filters)
    return success_response(data, request_id=get_request_id())


@phase9_router.post("/documents", response_model=ApiResponse[DocumentRead])
async def department_documents_upload_route(
    payload: DocumentUploadBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[DocumentRead]:
    data = await upload_document(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@phase9_router.get("/documents/{document_id}", response_model=ApiResponse[DocumentRead])
async def department_document_get_route(
    document_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[DocumentRead]:
    data = await get_document(scope, user, document_id)
    return success_response(data, request_id=get_request_id())


@phase9_router.patch("/documents/{document_id}", response_model=ApiResponse[DocumentRead])
async def department_document_patch_route(
    document_id: str,
    payload: DocumentUpdateBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[DocumentRead]:
    data = await update_document(scope, user, document_id, payload)
    return success_response(data, request_id=get_request_id())


@phase9_router.get("/documents/{document_id}/download", response_model=ApiResponse[DocumentDownloadRead])
async def department_document_download_route(
    document_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    version: Annotated[int | None, Query()] = None,
) -> ApiResponse[DocumentDownloadRead]:
    data = await download_document(scope, user, document_id, version_number=version)
    return success_response(data, request_id=get_request_id())


@phase9_router.post("/documents/{document_id}/versions", response_model=ApiResponse[DocumentRead])
async def department_document_version_create_route(
    document_id: str,
    payload: DocumentVersionBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[DocumentRead]:
    data = await create_document_version(scope, user, document_id, payload)
    return success_response(data, request_id=get_request_id())


@phase9_router.get("/documents/{document_id}/versions", response_model=ApiResponse[list[DocumentVersionRead]])
async def department_document_versions_route(
    document_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[list[DocumentVersionRead]]:
    data = await list_document_versions(scope, user, document_id)
    return success_response(data, request_id=get_request_id())


@phase9_router.post("/documents/{document_id}/archive", response_model=ApiResponse[DocumentRead])
async def department_document_archive_route(
    document_id: str,
    body: DocumentArchiveBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[DocumentRead]:
    data = await archive_document(scope, user, document_id, body)
    return success_response(data, request_id=get_request_id())


@phase9_router.get("/documents/{document_id}/history", response_model=ApiResponse[Page[DocumentHistoryRead]])
async def department_document_history_route(
    document_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[DocumentHistoryRead]]:
    data = await document_history(scope, user, document_id, pagination)
    return success_response(data, request_id=get_request_id())


@phase9_router.get("/audit", response_model=ApiResponse[Page[DepartmentAuditRead]])
async def department_audit_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    filters: Annotated[AuditListFilters, Depends(_audit_filters)],
) -> ApiResponse[Page[DepartmentAuditRead]]:
    data = await list_department_audit(scope, user, pagination, filters)
    return success_response(data, request_id=get_request_id())


@phase9_router.get("/audit/summary", response_model=ApiResponse[AuditSummaryRead])
async def department_audit_summary_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[AuditListFilters, Depends(_audit_filters)],
) -> ApiResponse[AuditSummaryRead]:
    data = await audit_summary(scope, user, filters)
    return success_response(data, request_id=get_request_id())


@phase9_router.get("/audit/approvals", response_model=ApiResponse[Page[DepartmentAuditRead]])
async def department_audit_approvals_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    filters: Annotated[AuditListFilters, Depends(_audit_filters)],
) -> ApiResponse[Page[DepartmentAuditRead]]:
    data = await approval_audit_history(scope, user, pagination, filters)
    return success_response(data, request_id=get_request_id())


@phase9_router.get("/audit/security-events", response_model=ApiResponse[Page[SecurityEventDeptRead]])
async def department_security_events_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[SecurityEventDeptRead]]:
    data = await list_department_security_events(scope, user, pagination)
    return success_response(data, request_id=get_request_id())


@phase9_router.get("/audit/configuration-history", response_model=ApiResponse[Page[ConfigurationChangeRead]])
async def department_configuration_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ConfigurationChangeRead]]:
    data = await configuration_change_history(scope, user, pagination)
    return success_response(data, request_id=get_request_id())


@phase9_router.get("/audit/permissions", response_model=ApiResponse[EffectivePermissionsRead])
async def department_effective_permissions_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[EffectivePermissionsRead]:
    data = effective_department_permissions(scope)
    return success_response(data, request_id=get_request_id())


@phase9_router.post("/audit/exports", response_model=ApiResponse[AuditExportRead])
async def department_audit_export_route(
    body: AuditExportBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[AuditExportRead]:
    data = await export_department_audit(scope, user, body)
    return success_response(data, request_id=get_request_id())


@phase9_router.get("/audit/{event_id}", response_model=ApiResponse[DepartmentAuditRead])
async def department_audit_get_route(
    event_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[DepartmentAuditRead]:
    data = await get_department_audit_event(scope, user, event_id)
    return success_response(data, request_id=get_request_id())