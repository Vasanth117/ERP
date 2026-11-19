"""Parent document dashboard, published reads, and access requests."""

import secrets
from datetime import timedelta
from uuid import uuid4

from beanie import PydanticObjectId

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.examinations.academic_document_models import AcademicDocumentPublication, AcademicDocumentStatus
from app.modules.finance.finance_models import PaymentReceipt
from app.modules.parents.enums import ParentDataPermission
from app.modules.parents.models import ParentDocumentAccessHistory, ParentDocumentAccessRequest
from app.modules.parents.phase4_schemas import (
    ParentDocumentAccessRequestCreate,
    ParentDocumentAccessRequestRead,
    ParentDocumentDashboardRead,
    ParentDocumentDownloadRead,
    ParentDocumentSummaryRead,
)
from app.modules.parents.policy import require_parent_scope
from app.modules.parents.relationship_access import require_student_access
from app.modules.parents.student_context import resolve_student_for_parent
from app.modules.students.integrations.academic_document_reader import published_document, published_documents
from app.modules.students.integrations.student_finance_reader import receipts_for_student


async def get_document_dashboard(scope: AccessScope, parent: User, student_user_id: str) -> ParentDocumentDashboardRead:
    authorize(scope, Permission.PARENT_DOCUMENT_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_RESULTS)
    academic = await published_documents(tenant_id, sid)
    receipts = []
    _, perms = await require_student_access(tenant_id, parent.id, sid, ParentDataPermission.VIEW_RECEIPTS)
    if perms and perms.grants.get(ParentDataPermission.VIEW_RECEIPTS.value, False):
        receipts = await receipts_for_student(tenant_id, sid)
    pending = await ParentDocumentAccessRequest.find(
        {"tenant_id": tenant_id, "parent_user_id": parent.id, "student_user_id": sid, "status": {"$in": ["submitted", "under_review"]}}
    ).count()
    return ParentDocumentDashboardRead(
        available_documents=len(academic) + len(receipts),
        recent_publications=sum(1 for d in academic if d.published_at and (utcnow() - d.published_at) < timedelta(days=30)),
        pending_requests=pending,
        awaiting_acknowledgement=0,
    )


async def list_documents(scope: AccessScope, parent: User, student_user_id: str) -> list[ParentDocumentSummaryRead]:
    authorize(scope, Permission.PARENT_DOCUMENT_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_PROFILE)
    items: list[ParentDocumentSummaryRead] = []

    if await _has_perm(tenant_id, parent.id, sid, ParentDataPermission.VIEW_RESULTS):
        for doc in await published_documents(tenant_id, sid):
            items.append(_academic_summary(doc))

    if await _has_perm(tenant_id, parent.id, sid, ParentDataPermission.VIEW_RECEIPTS):
        for r in await receipts_for_student(tenant_id, sid):
            items.append(
                ParentDocumentSummaryRead(
                    document_id=r.receipt_id,
                    document_category="financial",
                    document_type="fee_receipt",
                    title=f"Receipt {r.receipt_id}",
                    published_at=r.issued_at,
                )
            )

    items.sort(key=lambda x: x.published_at or utcnow(), reverse=True)
    return items


def _academic_summary(doc: AcademicDocumentPublication) -> ParentDocumentSummaryRead:
    return ParentDocumentSummaryRead(
        document_id=doc.document_id,
        document_category="academic",
        document_type=doc.document_type.value,
        title=doc.title,
        academic_year_label=doc.academic_year_label,
        semester_label=doc.semester_label,
        published_at=doc.published_at,
    )


async def _has_perm(tenant_id: PydanticObjectId, parent_id: PydanticObjectId, sid: PydanticObjectId, perm: ParentDataPermission) -> bool:
    try:
        await require_student_access(tenant_id, parent_id, sid, perm)
        return True
    except AppError:
        return False


async def get_document_detail(scope: AccessScope, parent: User, student_user_id: str, document_id: str) -> ParentDocumentSummaryRead:
    authorize(scope, Permission.PARENT_DOCUMENT_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_PROFILE)
    doc = await published_document(tenant_id, sid, document_id)
    if doc is not None and await _has_perm(tenant_id, parent.id, sid, ParentDataPermission.VIEW_RESULTS):
        return _academic_summary(doc)
    receipt = await PaymentReceipt.find_one(
        {"tenant_id": tenant_id, "student_user_id": sid, "receipt_id": document_id}
    )
    if receipt is not None and await _has_perm(tenant_id, parent.id, sid, ParentDataPermission.VIEW_RECEIPTS):
        return ParentDocumentSummaryRead(
            document_id=receipt.receipt_id,
            document_category="financial",
            document_type="fee_receipt",
            title=f"Receipt {receipt.receipt_id}",
            published_at=receipt.issued_at,
        )
    raise AppError(code="NOT_FOUND", message="Document not found or not authorized", status_code=404)


async def download_document(scope: AccessScope, parent: User, student_user_id: str, document_id: str) -> ParentDocumentDownloadRead:
    authorize(scope, Permission.PARENT_DOCUMENT_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_PROFILE)
    doc = await published_document(tenant_id, sid, document_id)
    if doc is None or doc.status != AcademicDocumentStatus.PUBLISHED:
        raise AppError(code="NOT_FOUND", message="Document not published", status_code=404)
    if not await _has_perm(tenant_id, parent.id, sid, ParentDataPermission.VIEW_RESULTS):
        raise AppError(code="FORBIDDEN", message="Document access not permitted", status_code=403)
    if not doc.storage_token:
        raise AppError(code="NOT_AVAILABLE", message="Download not yet available", status_code=503)
    token = secrets.token_urlsafe(32)
    expires = utcnow() + timedelta(minutes=15)
    await ParentDocumentAccessHistory(
        tenant_id=tenant_id,
        parent_user_id=parent.id,
        student_user_id=sid,
        document_id=document_id,
        document_category="academic",
        document_type=doc.document_type.value,
    ).insert()
    return ParentDocumentDownloadRead(
        document_id=document_id,
        document_type=doc.document_type.value,
        download_token=token,
        expires_at=expires,
    )


async def submit_document_access_request(
    scope: AccessScope, parent: User, student_user_id: str, payload: ParentDocumentAccessRequestCreate
) -> ParentDocumentAccessRequestRead:
    authorize(scope, Permission.PARENT_DOCUMENT_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.SUBMIT_SERVICE_REQUESTS)
    rel, _ = await require_student_access(tenant_id, parent.id, sid, ParentDataPermission.SUBMIT_SERVICE_REQUESTS)
    row = ParentDocumentAccessRequest(
        tenant_id=tenant_id,
        parent_user_id=parent.id,
        student_user_id=sid,
        relationship_id=rel.id,
        document_category=payload.document_category,
        document_type=payload.document_type,
        academic_year_label=payload.academic_year_label,
        semester_label=payload.semester_label,
        reason=payload.reason.strip(),
        status="submitted",
    )
    await row.insert()
    return ParentDocumentAccessRequestRead(
        request_id=str(row.id),
        document_category=row.document_category,
        document_type=row.document_type,
        status=row.status,
        reason=row.reason,
        created_at=row.created_at,
    )


async def list_document_access_requests(
    scope: AccessScope, parent: User, student_user_id: str
) -> list[ParentDocumentAccessRequestRead]:
    authorize(scope, Permission.PARENT_DOCUMENT_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_PROFILE)
    rows = await ParentDocumentAccessRequest.find(
        {"tenant_id": tenant_id, "parent_user_id": parent.id, "student_user_id": sid}
    ).sort("-created_at").to_list()
    return [
        ParentDocumentAccessRequestRead(
            request_id=str(r.id),
            document_category=r.document_category,
            document_type=r.document_type,
            status=r.status,
            reason=r.reason,
            response_notes=r.response_notes,
            created_at=r.created_at,
        )
        for r in rows
    ]