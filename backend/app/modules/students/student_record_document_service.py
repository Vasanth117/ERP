"""Read-only student record documents (admission / identity files on file)."""

from __future__ import annotations

import secrets
from datetime import timedelta

from beanie import PydanticObjectId

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.examinations.academic_document_models import AcademicDocumentStatus
from app.modules.students.integrations.academic_document_reader import published_document, published_documents
from app.modules.students.models import StudentProfile
from app.modules.students.policy import require_student_scope
from app.modules.students.student_portal_enums import StudentRecordDocumentCategory
from app.modules.students.student_portal_models import StudentDocumentReference
from app.modules.students.student_portal_schemas import (
    StudentRecordDocumentBulkDownloadRead,
    StudentRecordDocumentDownloadRead,
    StudentRecordDocumentRead,
)

_PROFILE_TYPE_CATEGORY: dict[str, StudentRecordDocumentCategory] = {
    "photo": StudentRecordDocumentCategory.IDENTITY,
    "aadhaar": StudentRecordDocumentCategory.IDENTITY,
    "identity": StudentRecordDocumentCategory.IDENTITY,
    "marksheet_10": StudentRecordDocumentCategory.ACADEMIC,
    "marksheet_12": StudentRecordDocumentCategory.ACADEMIC,
    "marksheet": StudentRecordDocumentCategory.ACADEMIC,
    "transfer_certificate": StudentRecordDocumentCategory.ADMISSION,
    "admission": StudentRecordDocumentCategory.ADMISSION,
}


def _category_label(category: str) -> str:
    try:
        return StudentRecordDocumentCategory(category).value
    except ValueError:
        return category


def _ref_read(row: StudentDocumentReference) -> StudentRecordDocumentRead:
    uploaded = row.uploaded_at or row.created_at
    return StudentRecordDocumentRead(
        document_id=row.document_id,
        title=row.title,
        category=_category_label(row.category),
        uploaded_at=uploaded,
        verified=row.verified,
        file_format=row.file_format.upper() if row.file_format else "PDF",
        download_available=bool(row.authorized and row.storage_token),
        source="record",
    )


async def list_record_documents(scope: AccessScope, user: User) -> list[StudentRecordDocumentRead]:
    authorize(scope, Permission.STUDENT_COMMUNICATION_READ)
    tenant_id = require_student_scope(scope)
    rows = await StudentDocumentReference.find(
        {"tenant_id": tenant_id, "user_id": user.id, "authorized": True}
    ).to_list()
    items = [_ref_read(r) for r in rows]
    seen = {i.document_id for i in items}

    for doc in await published_documents(tenant_id, user.id):
        if doc.document_id in seen:
            continue
        if doc.status != AcademicDocumentStatus.PUBLISHED:
            continue
        items.append(
            StudentRecordDocumentRead(
                document_id=doc.document_id,
                title=doc.title,
                category=StudentRecordDocumentCategory.ACADEMIC.value,
                uploaded_at=doc.published_at or doc.created_at,
                verified=True,
                file_format="PDF",
                download_available=bool(doc.storage_token),
                source="academic",
            )
        )
        seen.add(doc.document_id)

    profile = await StudentProfile.find_one({"tenant_id": tenant_id, "user_id": user.id})
    if profile:
        for ref in profile.document_refs:
            if not ref.authorized:
                continue
            doc_id = ref.file_id
            if doc_id in seen:
                continue
            cat = _PROFILE_TYPE_CATEGORY.get(ref.document_type, StudentRecordDocumentCategory.OTHER)
            fmt = "JPG" if ref.document_type == "photo" else "PDF"
            items.append(
                StudentRecordDocumentRead(
                    document_id=doc_id,
                    title=ref.label,
                    category=cat.value,
                    uploaded_at=profile.updated_at,
                    verified=True,
                    file_format=fmt,
                    download_available=False,
                    source="profile",
                )
            )
            seen.add(doc_id)

    items.sort(key=lambda x: x.uploaded_at or utcnow(), reverse=True)
    return items


async def download_record_document(
    scope: AccessScope,
    user: User,
    document_id: str,
) -> StudentRecordDocumentDownloadRead:
    authorize(scope, Permission.STUDENT_COMMUNICATION_READ)
    tenant_id = require_student_scope(scope)
    row = await StudentDocumentReference.find_one(
        {"tenant_id": tenant_id, "user_id": user.id, "document_id": document_id, "authorized": True}
    )
    if row is not None:
        if not row.storage_token:
            raise AppError(code="NOT_AVAILABLE", message="Download not available", status_code=503)
        token = secrets.token_urlsafe(32)
        expires_at = utcnow() + timedelta(minutes=15)
        row.last_viewed_at = utcnow()
        await row.save()
        file_name = None
        if row.storage_token.startswith("demo:"):
            file_name = row.storage_token.split(":", 1)[1]
        return StudentRecordDocumentDownloadRead(
            document_id=document_id,
            document_type=row.document_type,
            download_token=token,
            expires_at=expires_at,
            file_name=file_name,
        )

    academic = await published_document(tenant_id, user.id, document_id)
    if academic is not None and academic.storage_token:
        from app.modules.students.academic_document_service import download_academic_document

        academic_dl = await download_academic_document(scope, user, document_id)
        return StudentRecordDocumentDownloadRead(
            document_id=academic_dl.document_id,
            document_type=academic_dl.document_type,
            download_token=academic_dl.download_token,
            expires_at=academic_dl.expires_at,
            file_name=None,
        )

    raise AppError(code="NOT_FOUND", message="Document not found or not authorized", status_code=404)


async def download_all_record_documents(
    scope: AccessScope,
    user: User,
) -> StudentRecordDocumentBulkDownloadRead:
    items: list[StudentRecordDocumentDownloadRead] = []
    for row in await list_record_documents(scope, user):
        if not row.download_available:
            continue
        try:
            items.append(await download_record_document(scope, user, row.document_id))
        except AppError:
            continue
    return StudentRecordDocumentBulkDownloadRead(items=items)