"""Digital library and e-resources."""

import base64
import re
from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.library_admin_models import LibraryMembershipReference
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.library.digital_access import (
    authorize_digital_manage,
    authorize_digital_patron,
    authorize_digital_read,
    require_patron_tenant,
)
from app.modules.library.digital_enums import DigitalAccessAction, DigitalAvailabilityStatus, DigitalResourceType
from app.modules.library.digital_models import LibraryDigitalAccessLog
from app.modules.library.digital_schemas import (
    DigitalAccessLogEntry,
    DigitalDownloadRead,
    DigitalExternalLinkRead,
    DigitalFileUpload,
    DigitalResourceCreate,
    DigitalResourcePatronRead,
    DigitalResourceRead,
    DigitalResourceUpdate,
)
from app.modules.library.library_models import LibraryCatalogItem, LibraryDigitalResource
from app.modules.library.member_enums import LibraryMemberStatus
from app.modules.library.policy import require_library_tenant_scope
from app.modules.lms.storage import read_bytes, storage_key_for, validate_upload, write_bytes

_SAFE_URL = re.compile(r"^https?://", re.I)


def _resource_id(custom: str | None) -> str:
    if custom and custom.strip():
        return custom.strip()
    return f"dig_{uuid4().hex[:12]}"


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _license_valid(doc: LibraryDigitalResource) -> bool:
    if doc.availability_status == DigitalAvailabilityStatus.WITHDRAWN.value:
        return False
    if doc.availability_status == DigitalAvailabilityStatus.EXPIRED.value:
        return False
    if doc.license_expires_at and _as_utc(doc.license_expires_at) < utcnow():
        return False
    return True


def _sync_availability(doc: LibraryDigitalResource) -> None:
    if doc.license_expires_at and _as_utc(doc.license_expires_at) < utcnow():
        doc.availability_status = DigitalAvailabilityStatus.EXPIRED.value
    elif doc.availability_status == DigitalAvailabilityStatus.EXPIRED.value and _license_valid(doc):
        doc.availability_status = DigitalAvailabilityStatus.AVAILABLE.value


def _to_read(doc: LibraryDigitalResource) -> DigitalResourceRead:
    _sync_availability(doc)
    try:
        rtype = DigitalResourceType(doc.resource_type)
    except ValueError:
        rtype = DigitalResourceType.EBOOK
    try:
        avail = DigitalAvailabilityStatus(doc.availability_status)
    except ValueError:
        avail = DigitalAvailabilityStatus.AVAILABLE
    return DigitalResourceRead(
        resource_id=doc.resource_id,
        resource_type=rtype,
        title=doc.title,
        description=doc.description,
        category=doc.category,
        subcategory=doc.subcategory,
        authors=list(doc.authors or []),
        keywords=list(doc.keywords or []),
        book_id=doc.book_id,
        has_file=bool(doc.storage_key),
        has_external_link=bool(doc.url),
        mime_type=doc.mime_type,
        published=doc.published,
        availability_status=avail,
        license_type=doc.license_type,
        license_expires_at=doc.license_expires_at,
        license_valid=_license_valid(doc),
        allow_download=doc.allow_download,
        allow_external_link=doc.allow_external_link,
        requires_membership=doc.requires_membership,
        eligibility_member_categories=list(doc.eligibility_member_categories or []),
        download_count=doc.download_count,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


def _patron_read(doc: LibraryDigitalResource) -> DigitalResourcePatronRead:
    try:
        rtype = DigitalResourceType(doc.resource_type)
    except ValueError:
        rtype = DigitalResourceType.EBOOK
    return DigitalResourcePatronRead(
        resource_id=doc.resource_id,
        resource_type=rtype,
        title=doc.title,
        description=doc.description,
        category=doc.category,
        book_id=doc.book_id,
        allow_download=doc.allow_download and bool(doc.storage_key),
        allow_external_link=doc.allow_external_link and bool(doc.url),
        has_file=bool(doc.storage_key),
    )


async def _assert_book(tenant_id: PydanticObjectId, book_id: str | None) -> None:
    if not book_id:
        return
    item = await LibraryCatalogItem.find_one(Eq(LibraryCatalogItem.tenant_id, tenant_id), Eq(LibraryCatalogItem.book_id, book_id.strip()))
    if item is None:
        raise AppError(code="VALIDATION_ERROR", message="Unknown catalogue book_id", status_code=422)


async def _access_log(
    tenant_id: PydanticObjectId,
    *,
    resource_id: str,
    user_id: PydanticObjectId,
    action: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    await LibraryDigitalAccessLog(
        tenant_id=tenant_id,
        resource_id=resource_id,
        user_id=user_id,
        action=action,
        metadata=metadata or {},
    ).insert()


def _staff_can_preview_unpublished(scope: AccessScope) -> bool:
    return (
        Permission.LIBRARY_DIGITAL_MANAGE in scope.effective_permissions
        or Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions
        or scope.role == Role.COLLEGE_ADMIN
    )


async def _membership_ok(tenant_id: PydanticObjectId, user: User, doc: LibraryDigitalResource) -> bool:
    if not doc.requires_membership:
        return True
    if user.role in {Role.LIBRARIAN, Role.COLLEGE_ADMIN}:
        return True
    membership = await LibraryMembershipReference.find_one(
        Eq(LibraryMembershipReference.tenant_id, tenant_id),
        Eq(LibraryMembershipReference.member_user_id, user.id),
    )
    if membership is None:
        return False
    if not membership.eligible or membership.status != LibraryMemberStatus.ACTIVE.value:
        return False
    if membership.expires_on and membership.expires_on < date.today():
        return False
    if doc.eligibility_member_categories:
        if membership.member_category not in doc.eligibility_member_categories:
            return False
    return True


async def assert_resource_access(scope: AccessScope, user: User, resource_id: str, *, for_download: bool = False) -> LibraryDigitalResource:
    tenant_id = require_patron_tenant(scope)
    doc = await LibraryDigitalResource.find_one(
        Eq(LibraryDigitalResource.tenant_id, tenant_id),
        Eq(LibraryDigitalResource.resource_id, resource_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Digital resource not found", status_code=404)
    if not doc.published and not _staff_can_preview_unpublished(scope):
        raise AppError(code="FORBIDDEN", message="Resource is not published", status_code=403)
    _sync_availability(doc)
    if doc.published and not _license_valid(doc):
        raise AppError(code="FORBIDDEN", message="License has expired for this resource", status_code=403)
    if not await _membership_ok(tenant_id, user, doc):
        raise AppError(code="FORBIDDEN", message="Not eligible for this resource", status_code=403)
    if for_download:
        if not doc.allow_download or not doc.storage_key:
            raise AppError(code="FORBIDDEN", message="Downloads are not permitted", status_code=403)
        if doc.max_downloads is not None and doc.download_count >= doc.max_downloads:
            raise AppError(code="FORBIDDEN", message="Download limit reached for this resource", status_code=403)
        if doc.max_downloads_per_user is not None:
            count = await LibraryDigitalAccessLog.find(
                Eq(LibraryDigitalAccessLog.tenant_id, tenant_id),
                Eq(LibraryDigitalAccessLog.resource_id, resource_id),
                Eq(LibraryDigitalAccessLog.user_id, user.id),
                Eq(LibraryDigitalAccessLog.action, DigitalAccessAction.DOWNLOAD.value),
            ).count()
            if count >= doc.max_downloads_per_user:
                raise AppError(code="FORBIDDEN", message="Per-user download limit reached", status_code=403)
    return doc


async def register_digital_resource(scope: AccessScope, payload: DigitalResourceCreate) -> DigitalResourceRead:
    authorize_digital_manage(scope)
    tenant_id = require_library_tenant_scope(scope)
    rid = _resource_id(payload.resource_id)
    if await LibraryDigitalResource.find_one(Eq(LibraryDigitalResource.tenant_id, tenant_id), Eq(LibraryDigitalResource.resource_id, rid)):
        raise AppError(code="CONFLICT", message="Resource id already used", status_code=409)
    await _assert_book(tenant_id, payload.book_id)
    if payload.external_url and not _SAFE_URL.match(payload.external_url.strip()):
        raise AppError(code="VALIDATION_ERROR", message="External URL must use http or https", status_code=422)
    doc = LibraryDigitalResource(
        tenant_id=tenant_id,
        resource_id=rid,
        resource_type=payload.resource_type.value,
        title=payload.title.strip(),
        description=payload.description,
        category=payload.category.strip() if payload.category else None,
        subcategory=payload.subcategory.strip() if payload.subcategory else None,
        authors=[a.strip() for a in payload.authors if a.strip()],
        keywords=[k.strip() for k in payload.keywords if k.strip()],
        book_id=payload.book_id.strip() if payload.book_id else None,
        url=payload.external_url.strip() if payload.external_url else None,
        license_type=payload.license_type,
        license_expires_at=payload.license_expires_at,
        max_downloads=payload.max_downloads,
        max_downloads_per_user=payload.max_downloads_per_user,
        allow_download=payload.allow_download,
        allow_external_link=payload.allow_external_link,
        requires_membership=payload.requires_membership,
        eligibility_member_categories=[c.strip() for c in payload.eligibility_member_categories if c.strip()],
        published=payload.published,
        metadata=payload.metadata,
        created_by=scope.user_id,
    )
    await doc.insert()
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="library_digital.create",
        module="library_digital",
        resource_type="digital_resource",
        resource_id=rid,
    )
    return _to_read(doc)


async def update_digital_resource(scope: AccessScope, resource_id: str, payload: DigitalResourceUpdate) -> DigitalResourceRead:
    authorize_digital_manage(scope)
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryDigitalResource.find_one(
        Eq(LibraryDigitalResource.tenant_id, tenant_id),
        Eq(LibraryDigitalResource.resource_id, resource_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Digital resource not found", status_code=404)
    data = payload.model_dump(exclude_unset=True)
    if "external_url" in data:
        url = data.pop("external_url")
        if url and not _SAFE_URL.match(url.strip()):
            raise AppError(code="VALIDATION_ERROR", message="External URL must use http or https", status_code=422)
        doc.url = url.strip() if url else None
    if "book_id" in data:
        await _assert_book(tenant_id, data["book_id"])
        doc.book_id = data.pop("book_id")
    if "availability_status" in data:
        doc.availability_status = data.pop("availability_status").value
    for key, value in data.items():
        if key == "authors" and value is not None:
            doc.authors = [a.strip() for a in value if a.strip()]
        elif key == "keywords" and value is not None:
            doc.keywords = [k.strip() for k in value if k.strip()]
        elif key == "eligibility_member_categories" and value is not None:
            doc.eligibility_member_categories = [c.strip() for c in value if c.strip()]
        elif key == "metadata" and value is not None:
            doc.metadata = value
        elif hasattr(doc, key):
            setattr(doc, key, value)
    doc.updated_at = utcnow()
    await doc.save()
    return _to_read(doc)


async def upload_digital_file(scope: AccessScope, resource_id: str, payload: DigitalFileUpload) -> DigitalResourceRead:
    authorize_digital_manage(scope)
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryDigitalResource.find_one(
        Eq(LibraryDigitalResource.tenant_id, tenant_id),
        Eq(LibraryDigitalResource.resource_id, resource_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Digital resource not found", status_code=404)
    try:
        raw = base64.b64decode(payload.file_content_base64, validate=True)
    except Exception as exc:
        raise AppError(code="VALIDATION_ERROR", message="Invalid base64 file content", status_code=422) from exc
    validate_upload(payload.file_name, payload.mime_type, len(raw))
    storage_key = storage_key_for(str(tenant_id), "library_digital", payload.file_name)
    storage_key, checksum = write_bytes(storage_key, raw)
    doc.storage_key = storage_key
    doc.file_name = payload.file_name
    doc.checksum = checksum
    doc.file_size_bytes = len(raw)
    doc.mime_type = payload.mime_type
    doc.updated_at = utcnow()
    await doc.save()
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="library_digital.upload",
        module="library_digital",
        resource_type="digital_resource",
        resource_id=resource_id,
    )
    return _to_read(doc)


async def get_digital_resource(scope: AccessScope, resource_id: str) -> DigitalResourceRead:
    authorize_digital_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryDigitalResource.find_one(
        Eq(LibraryDigitalResource.tenant_id, tenant_id),
        Eq(LibraryDigitalResource.resource_id, resource_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Digital resource not found", status_code=404)
    return _to_read(doc)


async def search_digital_resources(
    scope: AccessScope,
    pagination: Pagination,
    *,
    q: str | None = None,
    category: str | None = None,
    resource_type: str | None = None,
    published: bool | None = None,
    book_id: str | None = None,
) -> Page[DigitalResourceRead]:
    authorize_digital_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    filters: dict[str, Any] = {"tenant_id": tenant_id}
    if category:
        filters["category"] = category.strip()
    if resource_type:
        filters["resource_type"] = resource_type.strip()
    if published is not None:
        filters["published"] = published
    if book_id:
        filters["book_id"] = book_id.strip()
    if q:
        filters["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"keywords": q},
        ]
    query = LibraryDigitalResource.find(filters).sort("-updated_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[_to_read(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def list_patron_digital_resources(scope: AccessScope, user: User, *, limit: int = 50) -> list[DigitalResourcePatronRead]:
    tenant_id = require_patron_tenant(scope)
    rows = await LibraryDigitalResource.find(
        {"tenant_id": tenant_id, "published": True, "availability_status": DigitalAvailabilityStatus.AVAILABLE.value}
    ).sort("title").limit(limit).to_list()
    items: list[DigitalResourcePatronRead] = []
    for doc in rows:
        _sync_availability(doc)
        if not _license_valid(doc):
            continue
        if not await _membership_ok(tenant_id, user, doc):
            continue
        items.append(_patron_read(doc))
    return items


async def download_digital_resource(scope: AccessScope, user: User, resource_id: str) -> DigitalDownloadRead:
    doc = await assert_resource_access(scope, user, resource_id, for_download=True)
    tenant_id = require_patron_tenant(scope)
    assert doc.storage_key
    data = read_bytes(doc.storage_key)
    doc.download_count += 1
    doc.updated_at = utcnow()
    await doc.save()
    await _access_log(tenant_id, resource_id=resource_id, user_id=user.id, action=DigitalAccessAction.DOWNLOAD.value)
    await append_institution_audit(
        tenant_id,
        actor_id=user.id,
        action="library_digital.download",
        module="library_digital",
        resource_type="digital_resource",
        resource_id=resource_id,
    )
    return DigitalDownloadRead(
        resource_id=resource_id,
        file_name=doc.file_name or f"{resource_id}.bin",
        content_type=doc.mime_type,
        content_base64=base64.b64encode(data).decode("ascii"),
        checksum=doc.checksum,
    )


async def external_link_for_resource(scope: AccessScope, user: User, resource_id: str) -> DigitalExternalLinkRead:
    doc = await assert_resource_access(scope, user, resource_id, for_download=False)
    tenant_id = require_patron_tenant(scope)
    if not doc.allow_external_link or not doc.url:
        raise AppError(code="FORBIDDEN", message="External access not permitted", status_code=403)
    if not _SAFE_URL.match(doc.url):
        raise AppError(code="FORBIDDEN", message="Invalid external link", status_code=403)
    await _access_log(tenant_id, resource_id=resource_id, user_id=user.id, action=DigitalAccessAction.EXTERNAL_LINK.value)
    return DigitalExternalLinkRead(resource_id=resource_id, url=doc.url)


async def record_digital_view(scope: AccessScope, user: User, resource_id: str) -> None:
    doc = await assert_resource_access(scope, user, resource_id, for_download=False)
    tenant_id = require_library_tenant_scope(scope)
    await _access_log(tenant_id, resource_id=doc.resource_id, user_id=user.id, action=DigitalAccessAction.VIEW.value)


async def digital_access_history(scope: AccessScope, resource_id: str, pagination: Pagination) -> Page[DigitalAccessLogEntry]:
    authorize_digital_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    exists = await LibraryDigitalResource.find_one(
        Eq(LibraryDigitalResource.tenant_id, tenant_id),
        Eq(LibraryDigitalResource.resource_id, resource_id),
    )
    if exists is None:
        raise AppError(code="NOT_FOUND", message="Digital resource not found", status_code=404)
    query = LibraryDigitalAccessLog.find(
        Eq(LibraryDigitalAccessLog.tenant_id, tenant_id),
        Eq(LibraryDigitalAccessLog.resource_id, resource_id),
    ).sort("-created_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    items = [
        DigitalAccessLogEntry(
            user_id=str(r.user_id),
            action=r.action,
            created_at=r.created_at,
            metadata=r.metadata,
        )
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def college_admin_add_digital_resource(scope: AccessScope, *, resource_id: str, title: str, url: str | None) -> dict:
    """Legacy college-admin query-param endpoint."""
    payload = DigitalResourceCreate(resource_id=resource_id, title=title, external_url=url, published=bool(url))
    read = await register_digital_resource(scope, payload)
    return {"resource_id": read.resource_id, "title": read.title}