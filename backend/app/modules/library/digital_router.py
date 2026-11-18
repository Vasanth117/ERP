"""Digital library routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.library.deps import librarian_user
from app.modules.library.digital_schemas import (
    DigitalAccessLogEntry,
    DigitalDownloadRead,
    DigitalExternalLinkRead,
    DigitalFileUpload,
    DigitalResourceCreate,
    DigitalResourceRead,
    DigitalResourceUpdate,
)
from app.modules.library.digital_service import (
    digital_access_history,
    download_digital_resource,
    external_link_for_resource,
    get_digital_resource,
    register_digital_resource,
    search_digital_resources,
    update_digital_resource,
    upload_digital_file,
)

router = APIRouter(prefix="/digital-resources", tags=["library-digital"])


@router.post("", response_model=ApiResponse[DigitalResourceRead], status_code=status.HTTP_201_CREATED)
async def register_digital_route(
    payload: DigitalResourceCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[DigitalResourceRead]:
    return success_response(await register_digital_resource(scope, payload), request_id=get_request_id())


@router.get("", response_model=ApiResponse[Page[DigitalResourceRead]])
async def search_digital_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    q: Annotated[str | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
    resource_type: Annotated[str | None, Query()] = None,
    published: Annotated[bool | None, Query()] = None,
    book_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[DigitalResourceRead]]:
    return success_response(
        await search_digital_resources(scope, pagination, q=q, category=category, resource_type=resource_type, published=published, book_id=book_id),
        request_id=get_request_id(),
    )


@router.get("/{resource_id}", response_model=ApiResponse[DigitalResourceRead])
async def get_digital_route(
    resource_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[DigitalResourceRead]:
    return success_response(await get_digital_resource(scope, resource_id), request_id=get_request_id())


@router.patch("/{resource_id}", response_model=ApiResponse[DigitalResourceRead])
async def update_digital_route(
    resource_id: str,
    payload: DigitalResourceUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[DigitalResourceRead]:
    return success_response(await update_digital_resource(scope, resource_id, payload), request_id=get_request_id())


@router.post("/{resource_id}/file", response_model=ApiResponse[DigitalResourceRead])
async def upload_digital_file_route(
    resource_id: str,
    payload: DigitalFileUpload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[DigitalResourceRead]:
    return success_response(await upload_digital_file(scope, resource_id, payload), request_id=get_request_id())


@router.get("/{resource_id}/access-log", response_model=ApiResponse[Page[DigitalAccessLogEntry]])
async def digital_access_history_route(
    resource_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[DigitalAccessLogEntry]]:
    return success_response(await digital_access_history(scope, resource_id, pagination), request_id=get_request_id())


@router.get("/{resource_id}/download", response_model=ApiResponse[DigitalDownloadRead])
async def download_digital_librarian_route(
    resource_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[DigitalDownloadRead]:
    return success_response(await download_digital_resource(scope, user, resource_id), request_id=get_request_id())


@router.get("/{resource_id}/external-link", response_model=ApiResponse[DigitalExternalLinkRead])
async def external_link_librarian_route(
    resource_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[DigitalExternalLinkRead]:
    return success_response(await external_link_for_resource(scope, user, resource_id), request_id=get_request_id())