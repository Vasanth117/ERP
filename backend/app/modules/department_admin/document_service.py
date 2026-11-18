"""Department Admin — document repository (metadata + LMS storage)."""

from __future__ import annotations

import base64
import re
from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, GTE, LTE, Ne

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.department_admin.audit_helpers import record_department_audit
from app.modules.auth.models import User
from app.modules.department_admin.document_constants import DOCUMENT_CATEGORIES
from app.modules.department_admin.models import (
    DepartmentDocument,
    DepartmentDocumentAccessScope,
    DepartmentDocumentHistory,
    DepartmentDocumentStatus,
    DepartmentDocumentVersion,
)
from app.modules.department_admin.phase9_schemas import (
    DocumentArchiveBody,
    DocumentDownloadRead,
    DocumentHistoryRead,
    DocumentListFilters,
    DocumentRead,
    DocumentUpdateBody,
    DocumentUploadBody,
    DocumentVersionBody,
    DocumentVersionRead,
)
from app.modules.department_admin.policy import resolve_authorized_department
from app.modules.lms.storage import read_bytes, storage_key_for, validate_upload, write_bytes


def _audit_meta(central_id: PydanticObjectId) -> dict:
    return {"central_department_id": str(central_id)}


def _document_read(doc: DepartmentDocument) -> DocumentRead:
    return DocumentRead(
        document_id=str(doc.id),
        title=doc.title,
        description=doc.description,
        category=doc.category,
        tags=doc.tags,
        access_scope=doc.access_scope,
        programme_code=doc.programme_code,
        batch_label=doc.batch_label,
        section_code=doc.section_code,
        authorized_user_ids=[str(uid) for uid in doc.authorized_user_ids],
        academic_year_label=doc.academic_year_label,
        related_entity_type=doc.related_entity_type,
        related_entity_id=doc.related_entity_id,
        status=doc.status,
        current_version=doc.current_version,
        file_name=doc.file_name,
        mime_type=doc.mime_type,
        file_size=doc.file_size,
        uploaded_by=str(doc.uploaded_by),
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        checksum=doc.checksum,
    )


def _version_read(row: DepartmentDocumentVersion) -> DocumentVersionRead:
    return DocumentVersionRead(
        version_id=str(row.id),
        version_number=row.version_number,
        file_name=row.file_name,
        mime_type=row.mime_type,
        file_size=row.file_size,
        checksum=row.checksum,
        uploaded_by=str(row.uploaded_by),
        update_reason=row.update_reason,
        created_at=row.created_at,
        previous_version_id=str(row.previous_version_id) if row.previous_version_id else None,
    )


async def _append_history(
    *,
    tenant_id: PydanticObjectId,
    central_id: PydanticObjectId,
    document_id: PydanticObjectId,
    event_type: str,
    actor: User | None,
    summary: str | None = None,
    metadata: dict | None = None,
) -> None:
    await DepartmentDocumentHistory(
        tenant_id=tenant_id,
        central_department_id=central_id,
        document_id=document_id,
        event_type=event_type,
        actor_user_id=actor.id if actor else None,
        summary=summary,
        metadata=metadata or {},
    ).insert()


def _validate_category(category: str) -> None:
    if category not in DOCUMENT_CATEGORIES:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Document category is not allowed",
            status_code=422,
            details=[{"field": "category", "allowed": sorted(DOCUMENT_CATEGORIES)}],
        )


def _validate_access_scope_fields(
    access_scope: DepartmentDocumentAccessScope,
    *,
    programme_code: str | None,
    batch_label: str | None,
    section_code: str | None,
    authorized_user_ids: list[PydanticObjectId],
) -> None:
    if access_scope == DepartmentDocumentAccessScope.PROGRAMME and not programme_code:
        raise AppError(code="VALIDATION_ERROR", message="programme_code is required for programme scope", status_code=422)
    if access_scope == DepartmentDocumentAccessScope.BATCH and not batch_label:
        raise AppError(code="VALIDATION_ERROR", message="batch_label is required for batch scope", status_code=422)
    if access_scope == DepartmentDocumentAccessScope.SECTION and not section_code:
        raise AppError(code="VALIDATION_ERROR", message="section_code is required for section scope", status_code=422)
    if access_scope == DepartmentDocumentAccessScope.EXPLICIT_USERS and not authorized_user_ids:
        raise AppError(code="VALIDATION_ERROR", message="authorized_user_ids required for explicit scope", status_code=422)


def _decode_file(payload: str) -> bytes:
    try:
        data = base64.b64decode(payload, validate=True)
    except Exception as exc:
        raise AppError(code="VALIDATION_ERROR", message="Invalid base64 file content", status_code=422) from exc
    if not data:
        raise AppError(code="VALIDATION_ERROR", message="Empty file content", status_code=422)
    return data


async def _get_document(
    tenant_id: PydanticObjectId,
    central_id: PydanticObjectId,
    document_id: str,
    *,
    include_deleted: bool = False,
) -> DepartmentDocument:
    doc = await DepartmentDocument.get(to_object_id(document_id, "document_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Document not found", status_code=404)
    if doc.status == DepartmentDocumentStatus.DELETED and not include_deleted:
        raise AppError(code="NOT_FOUND", message="Document not found", status_code=404)
    return doc


async def list_documents(
    scope: AccessScope,
    user: User,
    pagination: Pagination,
    filters: DocumentListFilters,
) -> Page[DocumentRead]:
    authorize(scope, Permission.DEPARTMENT_DOCUMENTS_READ)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None

    query = DepartmentDocument.find(
        Eq(DepartmentDocument.tenant_id, tenant_id),
        Eq(DepartmentDocument.central_department_id, central_id),
    )
    if filters.status is not None:
        query = query.find(Eq(DepartmentDocument.status, filters.status))
    else:
        query = query.find(Ne(DepartmentDocument.status, DepartmentDocumentStatus.DELETED))
    if filters.category:
        query = query.find(Eq(DepartmentDocument.category, filters.category))
    if filters.access_scope:
        query = query.find(Eq(DepartmentDocument.access_scope, filters.access_scope))
    if filters.academic_year_label:
        query = query.find(Eq(DepartmentDocument.academic_year_label, filters.academic_year_label))
    if filters.programme_code:
        query = query.find(Eq(DepartmentDocument.programme_code, filters.programme_code.upper()))
    if filters.uploaded_by:
        query = query.find(Eq(DepartmentDocument.uploaded_by, to_object_id(filters.uploaded_by, "uploaded_by")))
    if filters.date_from:
        query = query.find(GTE(DepartmentDocument.created_at, filters.date_from))
    if filters.date_to:
        query = query.find(LTE(DepartmentDocument.created_at, filters.date_to))
    if filters.tag:
        query = query.find({"tags": filters.tag.lower()})

    # Title search applied in memory (text index not assumed for phase 9).
    rows = await query.sort("-created_at").to_list()
    if filters.q:
        needle = filters.q.lower()
        rows = [r for r in rows if needle in r.title.lower() or (r.description or "").lower().find(needle) >= 0]
    total = len(rows)
    page_rows = rows[pagination.offset : pagination.offset + pagination.limit]
    return Page(
        items=[_document_read(r) for r in page_rows],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def upload_document(scope: AccessScope, user: User, payload: DocumentUploadBody) -> DocumentRead:
    authorize(scope, Permission.DEPARTMENT_DOCUMENTS_MANAGE)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None

    if payload.idempotency_key:
        existing = await DepartmentDocument.find_one(
            Eq(DepartmentDocument.tenant_id, tenant_id),
            Eq(DepartmentDocument.idempotency_key, payload.idempotency_key),
        )
        if existing is not None:
            return _document_read(existing)

    _validate_category(payload.category)
    auth_ids = [to_object_id(uid, "authorized_user_id") for uid in payload.authorized_user_ids]
    _validate_access_scope_fields(
        payload.access_scope,
        programme_code=payload.programme_code,
        batch_label=payload.batch_label,
        section_code=payload.section_code,
        authorized_user_ids=auth_ids,
    )

    data = _decode_file(payload.file_content_base64)
    validate_upload(payload.file_name, payload.mime_type, len(data))
    storage_key = storage_key_for(str(tenant_id), "dept_documents", payload.file_name)
    storage_key, checksum = write_bytes(storage_key, data)

    doc = DepartmentDocument(
        tenant_id=tenant_id,
        central_department_id=central_id,
        title=payload.title.strip(),
        description=payload.description,
        category=payload.category,
        tags=[t.lower()[:64] for t in payload.tags],
        access_scope=payload.access_scope,
        programme_code=payload.programme_code.upper() if payload.programme_code else None,
        batch_label=payload.batch_label,
        section_code=payload.section_code.upper() if payload.section_code else None,
        authorized_user_ids=auth_ids,
        academic_year_label=payload.academic_year_label,
        related_entity_type=payload.related_entity_type,
        related_entity_id=payload.related_entity_id,
        storage_key=storage_key,
        checksum=checksum,
        file_name=re.sub(r"[^a-zA-Z0-9._-]", "_", payload.file_name)[:256],
        mime_type=payload.mime_type,
        file_size=len(data),
        uploaded_by=user.id,
        idempotency_key=payload.idempotency_key,
    )
    await doc.insert()
    version = DepartmentDocumentVersion(
        tenant_id=tenant_id,
        central_department_id=central_id,
        document_id=doc.id,
        version_number=1,
        storage_key=storage_key,
        checksum=checksum,
        file_name=doc.file_name,
        mime_type=doc.mime_type,
        file_size=doc.file_size,
        uploaded_by=user.id,
    )
    await version.insert()
    await _append_history(
        tenant_id=tenant_id,
        central_id=central_id,
        document_id=doc.id,
        event_type="upload",
        actor=user,
        summary="Initial upload",
    )
    await record_department_audit(
        actor_id=user.id,
        action="department.document.uploaded",
        resource_type="department_document",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
        metadata=_audit_meta(central_id),
    )
    return _document_read(doc)


async def get_document(scope: AccessScope, user: User, document_id: str) -> DocumentRead:
    authorize(scope, Permission.DEPARTMENT_DOCUMENTS_READ)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await _get_document(tenant_id, central_id, document_id)
    return _document_read(doc)


async def update_document(
    scope: AccessScope,
    user: User,
    document_id: str,
    payload: DocumentUpdateBody,
) -> DocumentRead:
    authorize(scope, Permission.DEPARTMENT_DOCUMENTS_MANAGE)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await _get_document(tenant_id, central_id, document_id)
    if doc.status == DepartmentDocumentStatus.DELETED:
        raise AppError(code="FORBIDDEN", message="Deleted documents cannot be updated", status_code=403)

    before = {
        "title": doc.title,
        "access_scope": doc.access_scope.value,
        "status": doc.status.value,
    }
    if payload.title is not None:
        doc.title = payload.title.strip()
    if payload.description is not None:
        doc.description = payload.description
    if payload.category is not None:
        _validate_category(payload.category)
        doc.category = payload.category
    if payload.tags is not None:
        doc.tags = [t.lower()[:64] for t in payload.tags]
    if payload.access_scope is not None:
        doc.access_scope = payload.access_scope
    if payload.programme_code is not None:
        doc.programme_code = payload.programme_code.upper() or None
    if payload.batch_label is not None:
        doc.batch_label = payload.batch_label or None
    if payload.section_code is not None:
        doc.section_code = payload.section_code.upper() if payload.section_code else None
    if payload.authorized_user_ids is not None:
        doc.authorized_user_ids = [to_object_id(uid, "authorized_user_id") for uid in payload.authorized_user_ids]
    if payload.academic_year_label is not None:
        doc.academic_year_label = payload.academic_year_label
    if payload.related_entity_type is not None:
        doc.related_entity_type = payload.related_entity_type
    if payload.related_entity_id is not None:
        doc.related_entity_id = payload.related_entity_id
    if payload.status is not None:
        doc.status = payload.status

    _validate_access_scope_fields(
        doc.access_scope,
        programme_code=doc.programme_code,
        batch_label=doc.batch_label,
        section_code=doc.section_code,
        authorized_user_ids=doc.authorized_user_ids,
    )

    doc.updated_at = utcnow()
    await doc.save()
    await _append_history(
        tenant_id=tenant_id,
        central_id=central_id,
        document_id=doc.id,
        event_type="metadata_update",
        actor=user,
        summary="Metadata updated",
        metadata={"before": before, "after": {"title": doc.title, "access_scope": doc.access_scope.value, "status": doc.status.value}},
    )
    await record_department_audit(
        actor_id=user.id,
        action="department.document.updated",
        resource_type="department_document",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
        metadata=_audit_meta(central_id),
    )
    return _document_read(doc)


async def download_document(
    scope: AccessScope,
    user: User,
    document_id: str,
    *,
    version_number: int | None = None,
) -> DocumentDownloadRead:
    authorize(scope, Permission.DEPARTMENT_DOCUMENTS_READ)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await _get_document(tenant_id, central_id, document_id)
    if doc.status == DepartmentDocumentStatus.ARCHIVED:
        authorize(scope, Permission.DEPARTMENT_DOCUMENTS_MANAGE)

    if version_number is None or version_number == doc.current_version:
        storage_key = doc.storage_key
        file_name = doc.file_name
        mime_type = doc.mime_type
        checksum = doc.checksum
        ver = doc.current_version
    else:
        version_row = await DepartmentDocumentVersion.find_one(
            Eq(DepartmentDocumentVersion.tenant_id, tenant_id),
            Eq(DepartmentDocumentVersion.document_id, doc.id),
            Eq(DepartmentDocumentVersion.version_number, version_number),
        )
        if version_row is None:
            raise AppError(code="NOT_FOUND", message="Document version not found", status_code=404)
        storage_key = version_row.storage_key
        file_name = version_row.file_name
        mime_type = version_row.mime_type
        checksum = version_row.checksum
        ver = version_row.version_number

    data = read_bytes(storage_key)
    await _append_history(
        tenant_id=tenant_id,
        central_id=central_id,
        document_id=doc.id,
        event_type="download",
        actor=user,
        summary=f"Downloaded version {ver}",
    )
    await record_department_audit(
        actor_id=user.id,
        action="department.document.downloaded",
        resource_type="department_document",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
        metadata={**_audit_meta(central_id), "version": ver},
    )
    return DocumentDownloadRead(
        document_id=str(doc.id),
        version_number=ver,
        file_name=file_name,
        content_type=mime_type,
        content_base64=base64.b64encode(data).decode("ascii"),
        checksum=checksum,
    )


async def create_document_version(
    scope: AccessScope,
    user: User,
    document_id: str,
    payload: DocumentVersionBody,
) -> DocumentRead:
    authorize(scope, Permission.DEPARTMENT_DOCUMENTS_MANAGE)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await _get_document(tenant_id, central_id, document_id)
    if doc.status in {DepartmentDocumentStatus.DELETED, DepartmentDocumentStatus.ARCHIVED}:
        raise AppError(code="FORBIDDEN", message="Cannot version archived or deleted documents", status_code=403)

    data = _decode_file(payload.file_content_base64)
    validate_upload(payload.file_name, payload.mime_type, len(data))
    storage_key = storage_key_for(str(tenant_id), "dept_documents", payload.file_name)
    storage_key, checksum = write_bytes(storage_key, data)

    prev_version = await DepartmentDocumentVersion.find_one(
        Eq(DepartmentDocumentVersion.tenant_id, tenant_id),
        Eq(DepartmentDocumentVersion.document_id, doc.id),
        Eq(DepartmentDocumentVersion.version_number, doc.current_version),
    )
    new_number = doc.current_version + 1
    version = DepartmentDocumentVersion(
        tenant_id=tenant_id,
        central_department_id=central_id,
        document_id=doc.id,
        version_number=new_number,
        previous_version_id=prev_version.id if prev_version else None,
        storage_key=storage_key,
        checksum=checksum,
        file_name=re.sub(r"[^a-zA-Z0-9._-]", "_", payload.file_name)[:256],
        mime_type=payload.mime_type,
        file_size=len(data),
        uploaded_by=user.id,
        update_reason=payload.update_reason,
    )
    await version.insert()

    doc.current_version = new_number
    doc.storage_key = storage_key
    doc.checksum = checksum
    doc.file_name = version.file_name
    doc.mime_type = version.mime_type
    doc.file_size = version.file_size
    doc.updated_at = utcnow()
    await doc.save()

    await _append_history(
        tenant_id=tenant_id,
        central_id=central_id,
        document_id=doc.id,
        event_type="version_created",
        actor=user,
        summary=f"Version {new_number} created",
        metadata={"reason": payload.update_reason},
    )
    await record_department_audit(
        actor_id=user.id,
        action="department.document.version_created",
        resource_type="department_document",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
        metadata={**_audit_meta(central_id), "version": new_number},
    )
    return _document_read(doc)


async def list_document_versions(scope: AccessScope, user: User, document_id: str) -> list[DocumentVersionRead]:
    authorize(scope, Permission.DEPARTMENT_DOCUMENTS_READ)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await _get_document(tenant_id, central_id, document_id)
    rows = await DepartmentDocumentVersion.find(
        Eq(DepartmentDocumentVersion.tenant_id, tenant_id),
        Eq(DepartmentDocumentVersion.document_id, doc.id),
    ).sort("+version_number").to_list()
    return [_version_read(r) for r in rows]


async def archive_document(
    scope: AccessScope,
    user: User,
    document_id: str,
    body: DocumentArchiveBody,
) -> DocumentRead:
    authorize(scope, Permission.DEPARTMENT_DOCUMENTS_MANAGE)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await _get_document(tenant_id, central_id, document_id)
    if doc.status == DepartmentDocumentStatus.DELETED:
        raise AppError(code="FORBIDDEN", message="Document is deleted", status_code=403)
    doc.status = DepartmentDocumentStatus.ARCHIVED
    doc.updated_at = utcnow()
    await doc.save()
    await _append_history(
        tenant_id=tenant_id,
        central_id=central_id,
        document_id=doc.id,
        event_type="archive",
        actor=user,
        summary=body.reason or "Archived",
    )
    await record_department_audit(
        actor_id=user.id,
        action="department.document.archived",
        resource_type="department_document",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
        metadata=_audit_meta(central_id),
    )
    return _document_read(doc)


async def document_history(
    scope: AccessScope,
    user: User,
    document_id: str,
    pagination: Pagination,
) -> Page[DocumentHistoryRead]:
    authorize(scope, Permission.DEPARTMENT_DOCUMENTS_READ)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await _get_document(tenant_id, central_id, document_id)
    query = DepartmentDocumentHistory.find(
        Eq(DepartmentDocumentHistory.tenant_id, tenant_id),
        Eq(DepartmentDocumentHistory.document_id, doc.id),
    )
    total = await query.count()
    rows = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            DocumentHistoryRead(
                event_id=str(r.id),
                event_type=r.event_type,
                actor_user_id=str(r.actor_user_id) if r.actor_user_id else None,
                summary=r.summary,
                metadata=r.metadata,
                created_at=r.created_at,
            )
            for r in rows
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


def list_document_categories(scope: AccessScope) -> list[str]:
    authorize(scope, Permission.DEPARTMENT_DOCUMENTS_READ)
    return sorted(DOCUMENT_CATEGORIES)