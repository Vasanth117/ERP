"""Published marksheets, grade cards, transcripts (read + request + download)."""

import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.examinations.academic_document_models import AcademicDocumentType
from app.modules.students.academic_document_models import (
    StudentAcademicDocumentRequest,
    StudentDocumentDownloadLog,
    StudentGradeCardReference,
    StudentMarksheetReference,
    StudentTranscriptReference,
)
from app.modules.students.academic_document_schemas import (
    AcademicDocumentDownloadRead,
    AcademicDocumentHistoryRead,
    AcademicDocumentRequestCreate,
    AcademicDocumentRequestRead,
    AcademicDocumentSummaryRead,
)
from app.modules.students.academic_grading_enums import AcademicDocumentRequestType
from app.modules.students.integrations.academic_document_reader import (
    document_history_including_superseded,
    published_document,
    published_documents,
)
from app.modules.students.policy import require_student_scope

ALLOWED_REQUEST_TYPES = frozenset(t.value for t in AcademicDocumentRequestType)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _summary(doc) -> AcademicDocumentSummaryRead:
    return AcademicDocumentSummaryRead(
        document_id=doc.document_id,
        document_type=doc.document_type.value,
        title=doc.title,
        season_id=doc.season_id,
        academic_year_label=doc.academic_year_label,
        semester_label=doc.semester_label,
        version=doc.version,
        status=doc.status.value,
        gpa=doc.gpa,
        cgpa=doc.cgpa,
        published_at=doc.published_at,
        is_reissue=doc.replaces_document_id is not None,
    )


async def _touch_ref(tenant_id: PydanticObjectId, user_id: PydanticObjectId, doc) -> None:
    if doc.document_type == AcademicDocumentType.GRADE_CARD and doc.season_id:
        ref = await StudentGradeCardReference.find_one(
            {"tenant_id": tenant_id, "user_id": user_id, "season_id": doc.season_id}
        )
        if ref is None:
            await StudentGradeCardReference(
                tenant_id=tenant_id,
                user_id=user_id,
                document_id=doc.document_id,
                season_id=doc.season_id,
                last_viewed_at=_utcnow(),
            ).insert()
        else:
            ref.document_id = doc.document_id
            ref.last_viewed_at = _utcnow()
            await ref.save()
    elif doc.document_type == AcademicDocumentType.MARKSHEET:
        ref = await StudentMarksheetReference.find_one(
            {"tenant_id": tenant_id, "user_id": user_id, "document_id": doc.document_id}
        )
        if ref is None:
            await StudentMarksheetReference(
                tenant_id=tenant_id,
                user_id=user_id,
                document_id=doc.document_id,
                season_id=doc.season_id,
                last_viewed_at=_utcnow(),
            ).insert()
        else:
            ref.last_viewed_at = _utcnow()
            await ref.save()
    elif doc.document_type == AcademicDocumentType.TRANSCRIPT:
        ref = await StudentTranscriptReference.find_one({"tenant_id": tenant_id, "user_id": user_id})
        if ref is None:
            await StudentTranscriptReference(
                tenant_id=tenant_id,
                user_id=user_id,
                document_id=doc.document_id,
                last_viewed_at=_utcnow(),
            ).insert()
        else:
            ref.document_id = doc.document_id
            ref.last_viewed_at = _utcnow()
            await ref.save()


async def list_grade_cards(scope: AccessScope, user: User, season_id: str | None = None) -> list[AcademicDocumentSummaryRead]:
    authorize(scope, Permission.STUDENT_ACADEMIC_DOCUMENTS_READ)
    tenant_id = require_student_scope(scope)
    docs = await published_documents(
        tenant_id, user.id, document_type=AcademicDocumentType.GRADE_CARD, season_id=season_id
    )
    return [_summary(d) for d in docs]


async def list_marksheets(scope: AccessScope, user: User, season_id: str | None = None) -> list[AcademicDocumentSummaryRead]:
    authorize(scope, Permission.STUDENT_ACADEMIC_DOCUMENTS_READ)
    tenant_id = require_student_scope(scope)
    types = [AcademicDocumentType.MARKSHEET, AcademicDocumentType.CONSOLIDATED_MARKSHEET]
    docs: list = []
    for dtype in types:
        docs.extend(await published_documents(tenant_id, user.id, document_type=dtype, season_id=season_id))
    docs.sort(key=lambda d: d.published_at or d.created_at, reverse=True)
    return [_summary(d) for d in docs]


async def get_transcript(scope: AccessScope, user: User) -> AcademicDocumentSummaryRead:
    authorize(scope, Permission.STUDENT_ACADEMIC_DOCUMENTS_READ)
    tenant_id = require_student_scope(scope)
    docs = await published_documents(tenant_id, user.id, document_type=AcademicDocumentType.TRANSCRIPT)
    if not docs:
        semester_docs = await published_documents(
            tenant_id, user.id, document_type=AcademicDocumentType.SEMESTER_STATEMENT
        )
        if not semester_docs:
            raise AppError(code="NOT_FOUND", message="Transcript not published", status_code=404)
        doc = semester_docs[0]
    else:
        doc = docs[0]
    await _touch_ref(tenant_id, user.id, doc)
    return _summary(doc)


async def get_document_by_id(scope: AccessScope, user: User, document_id: str) -> AcademicDocumentSummaryRead:
    authorize(scope, Permission.STUDENT_ACADEMIC_DOCUMENTS_READ)
    tenant_id = require_student_scope(scope)
    doc = await published_document(tenant_id, user.id, document_id)
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Document not found", status_code=404)
    await _touch_ref(tenant_id, user.id, doc)
    return _summary(doc)


async def submit_document_request(
    scope: AccessScope, user: User, payload: AcademicDocumentRequestCreate
) -> AcademicDocumentRequestRead:
    authorize(scope, Permission.STUDENT_ACADEMIC_DOCUMENTS_REQUEST)
    tenant_id = require_student_scope(scope)
    if payload.request_type not in ALLOWED_REQUEST_TYPES:
        raise AppError(code="VALIDATION_ERROR", message="Invalid request type", status_code=422)
    request_id = f"docreq-{uuid4().hex[:12]}"
    row = StudentAcademicDocumentRequest(
        tenant_id=tenant_id,
        user_id=user.id,
        request_id=request_id,
        request_type=AcademicDocumentRequestType(payload.request_type),
        season_id=payload.season_id,
        reason=payload.reason,
    )
    await row.insert()
    await record_audit(
        actor_id=scope.user_id,
        action="student.academic_document.requested",
        resource_type="student_academic_document_request",
        resource_id=request_id,
        tenant_id=tenant_id,
    )
    return AcademicDocumentRequestRead(
        request_id=row.request_id,
        request_type=row.request_type.value,
        season_id=row.season_id,
        status=row.status.value,
        reason=row.reason,
        fulfilled_document_id=row.fulfilled_document_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def get_document_request_status(scope: AccessScope, user: User, request_id: str) -> AcademicDocumentRequestRead:
    authorize(scope, Permission.STUDENT_ACADEMIC_DOCUMENTS_READ)
    tenant_id = require_student_scope(scope)
    row = await StudentAcademicDocumentRequest.find_one(
        {"tenant_id": tenant_id, "user_id": user.id, "request_id": request_id}
    )
    if row is None:
        raise AppError(code="NOT_FOUND", message="Request not found", status_code=404)
    return AcademicDocumentRequestRead(
        request_id=row.request_id,
        request_type=row.request_type.value,
        season_id=row.season_id,
        status=row.status.value,
        reason=row.reason,
        fulfilled_document_id=row.fulfilled_document_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def download_academic_document(
    scope: AccessScope,
    user: User,
    document_id: str,
    *,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AcademicDocumentDownloadRead:
    authorize(scope, Permission.STUDENT_ACADEMIC_DOCUMENTS_READ)
    tenant_id = require_student_scope(scope)
    doc = await published_document(tenant_id, user.id, document_id)
    if doc is None:
        raise AppError(code="FORBIDDEN", message="Document not authorized", status_code=403)
    if not doc.storage_token:
        raise AppError(code="NOT_AVAILABLE", message="Download not available", status_code=503)
    token = secrets.token_urlsafe(32)
    expires_at = _utcnow() + timedelta(minutes=15)
    await StudentDocumentDownloadLog(
        tenant_id=tenant_id,
        user_id=user.id,
        document_id=document_id,
        document_type=doc.document_type.value,
        ip_address=ip_address,
        user_agent=user_agent,
    ).insert()
    await record_audit(
        actor_id=scope.user_id,
        action="student.academic_document.downloaded",
        resource_type="academic_document_publication",
        resource_id=document_id,
        tenant_id=tenant_id,
    )
    return AcademicDocumentDownloadRead(
        document_id=document_id,
        document_type=doc.document_type.value,
        download_token=token,
        expires_at=expires_at,
    )


async def document_access_history(scope: AccessScope, user: User, pagination: Pagination) -> Page[AcademicDocumentHistoryRead]:
    authorize(scope, Permission.STUDENT_ACADEMIC_DOCUMENTS_READ)
    tenant_id = require_student_scope(scope)
    docs = await document_history_including_superseded(tenant_id, user.id)
    published = [d for d in docs if d.status.value == "published" or d.status.value == "superseded"]
    logs = await StudentDocumentDownloadLog.find({"tenant_id": tenant_id, "user_id": user.id}).sort("-downloaded_at").to_list()
    log_by_doc = {l.document_id: l.downloaded_at for l in logs}
    items = [
        AcademicDocumentHistoryRead(
            document_id=d.document_id,
            document_type=d.document_type.value,
            title=d.title,
            version=d.version,
            published_at=d.published_at,
            downloaded_at=log_by_doc.get(d.document_id),
        )
        for d in published
    ]
    slice_items = items[pagination.offset : pagination.offset + pagination.limit]
    return Page(items=slice_items, total=len(items), limit=pagination.limit, offset=pagination.offset)
