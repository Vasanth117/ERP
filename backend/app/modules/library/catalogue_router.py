"""Book catalogue management routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.library.catalogue_enums import CatalogueSortField, CatalogueSortOrder
from app.modules.library.catalogue_schemas import (
    CatalogueBulkImportRequest,
    CatalogueBulkImportResult,
    CatalogueDuplicateCheckResult,
    CatalogueHistoryEntry,
    CatalogueRecordCreate,
    CatalogueRecordRead,
    CatalogueRecordUpdate,
)
from app.modules.library.catalogue_service import (
    archive_catalogue_record,
    bulk_import_catalogue,
    catalogue_history,
    check_duplicates,
    create_catalogue_record,
    get_catalogue_record,
    search_catalogue_records,
    update_catalogue_record,
)
from app.modules.library.deps import librarian_user

router = APIRouter(prefix="/catalogue", tags=["library-catalogue"])


@router.post("/records", response_model=ApiResponse[CatalogueRecordRead], status_code=status.HTTP_201_CREATED)
async def catalogue_create_route(
    payload: CatalogueRecordCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[CatalogueRecordRead]:
    return success_response(await create_catalogue_record(scope, payload), request_id=get_request_id())


@router.get("/records", response_model=ApiResponse[Page[CatalogueRecordRead]])
async def catalogue_search_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    q: Annotated[str | None, Query(description="Search title, authors, ISBN, keywords, tags")] = None,
    category: Annotated[str | None, Query()] = None,
    subcategory: Annotated[str | None, Query()] = None,
    language: Annotated[str | None, Query()] = None,
    primary_library_code: Annotated[str | None, Query()] = None,
    include_archived: Annotated[bool, Query()] = False,
    sort_by: Annotated[CatalogueSortField, Query()] = CatalogueSortField.TITLE,
    sort_order: Annotated[CatalogueSortOrder, Query()] = CatalogueSortOrder.ASC,
) -> ApiResponse[Page[CatalogueRecordRead]]:
    data = await search_catalogue_records(
        scope,
        pagination,
        q=q,
        category=category,
        subcategory=subcategory,
        language=language,
        primary_library_code=primary_library_code,
        include_archived=include_archived,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/records/{book_id}", response_model=ApiResponse[CatalogueRecordRead])
async def catalogue_get_route(
    book_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[CatalogueRecordRead]:
    return success_response(await get_catalogue_record(scope, book_id), request_id=get_request_id())


@router.patch("/records/{book_id}", response_model=ApiResponse[CatalogueRecordRead])
async def catalogue_update_route(
    book_id: str,
    payload: CatalogueRecordUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[CatalogueRecordRead]:
    return success_response(await update_catalogue_record(scope, book_id, payload), request_id=get_request_id())


@router.post("/records/{book_id}/archive", response_model=ApiResponse[CatalogueRecordRead])
async def catalogue_archive_route(
    book_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[CatalogueRecordRead]:
    return success_response(await archive_catalogue_record(scope, book_id), request_id=get_request_id())


@router.get("/duplicates", response_model=ApiResponse[CatalogueDuplicateCheckResult])
async def catalogue_duplicates_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    isbn: Annotated[str | None, Query()] = None,
    isbn13: Annotated[str | None, Query()] = None,
    title: Annotated[str | None, Query()] = None,
    publisher: Annotated[str | None, Query()] = None,
    edition: Annotated[str | None, Query()] = None,
    exclude_book_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[CatalogueDuplicateCheckResult]:
    return success_response(
        await check_duplicates(
            scope,
            isbn=isbn,
            isbn13=isbn13,
            title=title,
            publisher=publisher,
            edition=edition,
            exclude_book_id=exclude_book_id,
        ),
        request_id=get_request_id(),
    )


@router.post("/import", response_model=ApiResponse[CatalogueBulkImportResult])
async def catalogue_bulk_import_route(
    payload: CatalogueBulkImportRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[CatalogueBulkImportResult]:
    return success_response(await bulk_import_catalogue(scope, payload), request_id=get_request_id())


@router.get("/records/{book_id}/history", response_model=ApiResponse[Page[CatalogueHistoryEntry]])
async def catalogue_history_route(
    book_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[CatalogueHistoryEntry]]:
    return success_response(await catalogue_history(scope, book_id, pagination), request_id=get_request_id())