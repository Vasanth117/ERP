"""Book catalogue management services."""

from typing import Any

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.library.catalogue_access import authorize_catalogue_manage, require_catalogue_tenant
from app.modules.library.catalogue_enums import CatalogueSortField, CatalogueSortOrder
from app.modules.library.catalogue_isbn import normalize_isbn10, normalize_isbn13, validate_cover_reference
from app.modules.library.catalogue_repository import CatalogueRepository
from app.modules.library.catalogue_schemas import (
    CatalogueBulkImportRequest,
    CatalogueBulkImportError,
    CatalogueBulkImportResult,
    CatalogueDuplicateCheckResult,
    CatalogueDuplicateMatch,
    CatalogueHistoryEntry,
    CatalogueRecordCreate,
    CatalogueRecordRead,
    CatalogueRecordUpdate,
)
from app.modules.library.facility_models import InstitutionLibrary
from app.modules.library.library_models import LibraryCatalogItem

_repo = CatalogueRepository()


def _norm_library_code(code: str | None) -> str | None:
    return code.strip().upper() if code else None


async def _assert_library_code(tenant_id: PydanticObjectId, library_code: str | None) -> None:
    if not library_code:
        return
    exists = await InstitutionLibrary.find_one(
        Eq(InstitutionLibrary.tenant_id, tenant_id),
        Eq(InstitutionLibrary.library_code, _norm_library_code(library_code)),
    )
    if exists is None:
        raise AppError(code="VALIDATION_ERROR", message="Unknown primary_library_code", status_code=422)


def _to_read(doc: LibraryCatalogItem) -> CatalogueRecordRead:
    return CatalogueRecordRead(
        book_id=doc.book_id,
        isbn=doc.isbn,
        isbn13=doc.isbn13,
        title=doc.title,
        subtitle=doc.subtitle,
        authors=list(doc.authors),
        publisher=doc.publisher,
        publication_year=doc.publication_year,
        publication_place=doc.publication_place,
        edition=doc.edition,
        volume=doc.volume,
        language=doc.language,
        category=doc.category,
        subcategory=doc.subcategory,
        subject=doc.subject,
        academic_classification=doc.academic_classification,
        keywords=list(doc.keywords),
        tags=list(doc.tags),
        description=doc.description,
        metadata=dict(doc.metadata),
        cover_storage_key=doc.cover_storage_key,
        cover_url=doc.cover_url,
        primary_library_code=doc.primary_library_code,
        archived=doc.archived,
        published=doc.published,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


def _snapshot(doc: LibraryCatalogItem) -> dict[str, Any]:
    data = doc.model_dump(mode="json")
    data.pop("id", None)
    data.pop("revision_id", None)
    return data


async def _ensure_no_isbn_conflict(
    tenant_id: PydanticObjectId,
    *,
    isbn: str | None,
    isbn13: str | None,
    exclude_book_id: str | None,
) -> None:
    existing = await _repo.find_by_isbn(tenant_id, isbn=isbn, isbn13=isbn13)
    if existing and (exclude_book_id is None or existing.book_id != exclude_book_id):
        raise AppError(code="CONFLICT", message="Catalogue record with this ISBN already exists", status_code=409)


async def create_catalogue_record(scope: AccessScope, payload: CatalogueRecordCreate) -> CatalogueRecordRead:
    authorize_catalogue_manage(scope)
    tenant_id = require_catalogue_tenant(scope)
    book_id = payload.book_id.strip()
    if await _repo.get_by_book_id(tenant_id, book_id):
        raise AppError(code="CONFLICT", message="book_id already exists", status_code=409)
    isbn = normalize_isbn10(payload.isbn)
    isbn13 = normalize_isbn13(payload.isbn13)
    validate_cover_reference(cover_url=payload.cover_url, cover_storage_key=payload.cover_storage_key)
    await _assert_library_code(tenant_id, payload.primary_library_code)
    await _ensure_no_isbn_conflict(tenant_id, isbn=isbn, isbn13=isbn13, exclude_book_id=None)
    lib_code = _norm_library_code(payload.primary_library_code)
    doc = LibraryCatalogItem(
        tenant_id=tenant_id,
        book_id=book_id,
        isbn=isbn,
        isbn13=isbn13,
        title=payload.title.strip(),
        subtitle=payload.subtitle,
        authors=payload.authors,
        publisher=payload.publisher,
        publication_year=payload.publication_year,
        publication_place=payload.publication_place,
        edition=payload.edition,
        volume=payload.volume,
        language=payload.language,
        category=payload.category,
        subcategory=payload.subcategory,
        subject=payload.subject,
        academic_classification=payload.academic_classification,
        keywords=[k.strip() for k in payload.keywords if k.strip()],
        tags=[t.strip() for t in payload.tags if t.strip()],
        description=payload.description,
        metadata=payload.metadata,
        cover_storage_key=payload.cover_storage_key,
        cover_url=payload.cover_url,
        primary_library_code=lib_code,
        published=payload.published,
        archived=False,
        created_by=scope.user_id,
        updated_by=scope.user_id,
    )
    await doc.insert()
    await _repo.append_history(tenant_id, book_id=book_id, action="create", actor_id=scope.user_id, snapshot=_snapshot(doc))
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="library_catalogue.create",
        module="library_catalogue",
        resource_type="catalogue",
        resource_id=book_id,
    )
    return _to_read(doc)


async def get_catalogue_record(scope: AccessScope, book_id: str) -> CatalogueRecordRead:
    tenant_id = require_catalogue_tenant(scope)
    doc = await _repo.get_by_book_id(tenant_id, book_id)
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Catalogue record not found", status_code=404)
    return _to_read(doc)


async def update_catalogue_record(scope: AccessScope, book_id: str, payload: CatalogueRecordUpdate) -> CatalogueRecordRead:
    authorize_catalogue_manage(scope)
    tenant_id = require_catalogue_tenant(scope)
    doc = await _repo.get_by_book_id(tenant_id, book_id)
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Catalogue record not found", status_code=404)
    unset = payload.model_dump(exclude_unset=True)
    if not unset:
        raise AppError(code="VALIDATION_ERROR", message="No fields to update", status_code=422)
    changes: dict[str, Any] = dict(unset)
    if payload.isbn is not None:
        doc.isbn = normalize_isbn10(payload.isbn)
    if payload.isbn13 is not None:
        doc.isbn13 = normalize_isbn13(payload.isbn13)
    if payload.isbn is not None or payload.isbn13 is not None:
        await _ensure_no_isbn_conflict(tenant_id, isbn=doc.isbn, isbn13=doc.isbn13, exclude_book_id=doc.book_id)
    if payload.title is not None:
        doc.title = payload.title.strip()
    if payload.subtitle is not None:
        doc.subtitle = payload.subtitle
    if payload.authors is not None:
        doc.authors = [a.strip() for a in payload.authors if a.strip()]
    if payload.publisher is not None:
        doc.publisher = payload.publisher
    if payload.publication_year is not None:
        doc.publication_year = payload.publication_year
    if payload.publication_place is not None:
        doc.publication_place = payload.publication_place
    if payload.edition is not None:
        doc.edition = payload.edition
    if payload.volume is not None:
        doc.volume = payload.volume
    if payload.language is not None:
        doc.language = payload.language
    if payload.category is not None:
        doc.category = payload.category
    if payload.subcategory is not None:
        doc.subcategory = payload.subcategory
    if payload.subject is not None:
        doc.subject = payload.subject
    if payload.academic_classification is not None:
        doc.academic_classification = payload.academic_classification
    if payload.keywords is not None:
        doc.keywords = [k.strip() for k in payload.keywords if k.strip()]
    if payload.tags is not None:
        doc.tags = [t.strip() for t in payload.tags if t.strip()]
    if payload.description is not None:
        doc.description = payload.description
    if payload.metadata is not None:
        doc.metadata = payload.metadata
    if payload.cover_storage_key is not None or payload.cover_url is not None:
        validate_cover_reference(
            cover_url=payload.cover_url if payload.cover_url is not None else doc.cover_url,
            cover_storage_key=payload.cover_storage_key if payload.cover_storage_key is not None else doc.cover_storage_key,
        )
        if payload.cover_storage_key is not None:
            doc.cover_storage_key = payload.cover_storage_key
        if payload.cover_url is not None:
            doc.cover_url = payload.cover_url
    if payload.primary_library_code is not None:
        await _assert_library_code(tenant_id, payload.primary_library_code)
        doc.primary_library_code = _norm_library_code(payload.primary_library_code)
    if payload.published is not None:
        doc.published = payload.published
    doc.updated_by = scope.user_id
    doc.updated_at = utcnow()
    await doc.save()
    await _repo.append_history(tenant_id, book_id=doc.book_id, action="update", actor_id=scope.user_id, snapshot=changes)
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="library_catalogue.update",
        module="library_catalogue",
        resource_type="catalogue",
        resource_id=doc.book_id,
        metadata=changes,
    )
    return _to_read(doc)


async def archive_catalogue_record(scope: AccessScope, book_id: str) -> CatalogueRecordRead:
    authorize_catalogue_manage(scope)
    tenant_id = require_catalogue_tenant(scope)
    doc = await _repo.get_by_book_id(tenant_id, book_id)
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Catalogue record not found", status_code=404)
    if doc.archived:
        raise AppError(code="CONFLICT", message="Catalogue record already archived", status_code=409)
    doc.archived = True
    doc.published = False
    doc.updated_by = scope.user_id
    doc.updated_at = utcnow()
    await doc.save()
    await _repo.append_history(tenant_id, book_id=book_id, action="archive", actor_id=scope.user_id, snapshot={"archived": True})
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="library_catalogue.archive",
        module="library_catalogue",
        resource_type="catalogue",
        resource_id=book_id,
    )
    return _to_read(doc)


async def search_catalogue_records(
    scope: AccessScope,
    pagination: Pagination,
    *,
    q: str | None = None,
    category: str | None = None,
    subcategory: str | None = None,
    language: str | None = None,
    primary_library_code: str | None = None,
    include_archived: bool = False,
    sort_by: CatalogueSortField = CatalogueSortField.TITLE,
    sort_order: CatalogueSortOrder = CatalogueSortOrder.ASC,
) -> Page[CatalogueRecordRead]:
    tenant_id = require_catalogue_tenant(scope)
    rows, total = await _repo.search(
        tenant_id,
        q=q,
        category=category,
        subcategory=subcategory,
        language=language,
        primary_library_code=primary_library_code,
        include_archived=include_archived,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return Page(items=[_to_read(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def check_duplicates(
    scope: AccessScope,
    *,
    isbn: str | None = None,
    isbn13: str | None = None,
    title: str | None = None,
    publisher: str | None = None,
    edition: str | None = None,
    exclude_book_id: str | None = None,
) -> CatalogueDuplicateCheckResult:
    tenant_id = require_catalogue_tenant(scope)
    matches: list[CatalogueDuplicateMatch] = []
    isbn_norm = normalize_isbn10(isbn) if isbn else None
    isbn13_norm = normalize_isbn13(isbn13) if isbn13 else None
    if isbn_norm or isbn13_norm:
        row = await _repo.find_by_isbn(tenant_id, isbn=isbn_norm, isbn13=isbn13_norm)
        if row and row.book_id != exclude_book_id:
            reason = "isbn" if isbn_norm and row.isbn == isbn_norm else "isbn13"
            matches.append(CatalogueDuplicateMatch(book_id=row.book_id, title=row.title, match_reason=reason))
    if title and publisher:
        filters: dict[str, Any] = {
            "tenant_id": tenant_id,
            "title": title.strip(),
            "publisher": publisher.strip(),
            "archived": False,
        }
        if edition:
            filters["edition"] = edition.strip()
        rows = await LibraryCatalogItem.find(filters).to_list()
        for row in rows:
            if exclude_book_id and row.book_id == exclude_book_id:
                continue
            matches.append(
                CatalogueDuplicateMatch(
                    book_id=row.book_id,
                    title=row.title,
                    match_reason="title_publisher_edition",
                )
            )
    return CatalogueDuplicateCheckResult(duplicates=matches)


async def bulk_import_catalogue(scope: AccessScope, payload: CatalogueBulkImportRequest) -> CatalogueBulkImportResult:
    authorize_catalogue_manage(scope)
    tenant_id = require_catalogue_tenant(scope)
    created = updated = skipped = 0
    errors: list[CatalogueBulkImportError] = []
    for idx, item in enumerate(payload.items):
        try:
            book_id = item.book_id.strip()
            existing = await _repo.get_by_book_id(tenant_id, book_id)
            isbn = normalize_isbn10(item.isbn)
            isbn13 = normalize_isbn13(item.isbn13)
            validate_cover_reference(cover_url=item.cover_url, cover_storage_key=item.cover_storage_key)
            await _assert_library_code(tenant_id, item.primary_library_code)
            await _ensure_no_isbn_conflict(
                tenant_id,
                isbn=isbn,
                isbn13=isbn13,
                exclude_book_id=book_id if existing else None,
            )
            if existing and not payload.update_existing:
                skipped += 1
                continue
            if payload.dry_run:
                if existing:
                    updated += 1
                else:
                    created += 1
                continue
            if existing:
                await update_catalogue_record(
                    scope,
                    book_id,
                    CatalogueRecordUpdate(
                        title=item.title,
                        subtitle=item.subtitle,
                        isbn=isbn,
                        isbn13=isbn13,
                        authors=item.authors,
                        publisher=item.publisher,
                        publication_year=item.publication_year,
                        publication_place=item.publication_place,
                        edition=item.edition,
                        volume=item.volume,
                        language=item.language,
                        category=item.category,
                        subcategory=item.subcategory,
                        subject=item.subject,
                        academic_classification=item.academic_classification,
                        keywords=item.keywords,
                        tags=item.tags,
                        description=item.description,
                        metadata=item.metadata,
                        cover_storage_key=item.cover_storage_key,
                        cover_url=item.cover_url,
                        primary_library_code=item.primary_library_code,
                        published=item.published,
                    ),
                )
                updated += 1
            else:
                await create_catalogue_record(scope, item)
                created += 1
        except AppError as exc:
            errors.append(CatalogueBulkImportError(row=idx, book_id=item.book_id, message=exc.message))
        except Exception as exc:  # noqa: BLE001
            errors.append(CatalogueBulkImportError(row=idx, book_id=item.book_id, message=str(exc)))
    return CatalogueBulkImportResult(created=created, updated=updated, skipped=skipped, errors=errors, dry_run=payload.dry_run)


async def catalogue_history(
    scope: AccessScope,
    book_id: str,
    pagination: Pagination,
) -> Page[CatalogueHistoryEntry]:
    tenant_id = require_catalogue_tenant(scope)
    if await _repo.get_by_book_id(tenant_id, book_id) is None:
        raise AppError(code="NOT_FOUND", message="Catalogue record not found", status_code=404)
    rows, total = await _repo.list_history(tenant_id, book_id, limit=pagination.limit, offset=pagination.offset)
    items = [
        CatalogueHistoryEntry(
            action=r.action,
            actor_id=str(r.actor_id) if r.actor_id else None,
            snapshot=r.snapshot,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)