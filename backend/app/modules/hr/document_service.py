"""HR employee document management."""

from datetime import date, timedelta
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In
from fastapi import UploadFile

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.hr.document_models import (
    HrDocumentCategory,
    HrDocumentExpiryPolicy,
    HrEmployeeDocument,
    HrEmployeeDocumentEvent,
    HrMandatoryDocumentRule,
)
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
from app.modules.hr.employee_profile_models import HrEmployeeProfile
from app.modules.hr.enums import HrEmployeeDocumentStatus
from app.modules.hr.policy import (
    authorize_hr_document_manage,
    authorize_hr_document_read,
    authorize_hr_document_verify,
    authorize_hr_portal,
    require_hr_tenant_scope,
)
from app.modules.lms import storage as file_storage

_DEFAULT_CATEGORIES: list[tuple[str, str, str, bool]] = [
    ("GOV_ID", "Government identity proof", "identity", True),
    ("ADDRESS_PROOF", "Address proof", "identity", True),
    ("DEGREE", "Degree certificate", "education", False),
    ("MARKSHEET", "Mark sheet", "education", False),
    ("EXPERIENCE", "Experience letter", "employment", False),
    ("APPOINTMENT", "Appointment letter", "employment", False),
    ("CONTRACT", "Employment contract", "employment", True),
    ("PHOTO", "Photograph", "personal", False),
    ("BANK_PROOF", "Bank account proof", "financial", True),
    ("TAX_DECL", "Tax declaration", "financial", True),
]


async def _seed_categories(tenant_id: PydanticObjectId) -> None:
    if await HrDocumentCategory.find(Eq(HrDocumentCategory.tenant_id, tenant_id)).count():
        return
    for code, name, group, sensitive in _DEFAULT_CATEGORIES:
        await HrDocumentCategory(
            tenant_id=tenant_id,
            category_code=code,
            name=name,
            parent_group=group,
            is_sensitive=sensitive,
        ).insert()


async def _log_doc_event(
    tenant_id: PydanticObjectId,
    doc: HrEmployeeDocument,
    event_type: str,
    *,
    status_from: str | None,
    status_to: str | None,
    note: str | None,
    actor_id: PydanticObjectId | None,
) -> None:
    await HrEmployeeDocumentEvent(
        tenant_id=tenant_id,
        document_id=doc.id,
        employee_user_id=doc.employee_user_id,
        event_type=event_type,
        status_from=status_from,
        status_to=status_to,
        note=note,
        actor_id=actor_id,
    ).insert()


async def list_document_categories(scope: AccessScope) -> list[HrDocumentCategoryRead]:
    authorize_hr_document_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    await _seed_categories(tenant_id)
    rows = await HrDocumentCategory.find(Eq(HrDocumentCategory.tenant_id, tenant_id), Eq(HrDocumentCategory.is_active, True)).to_list()
    return [HrDocumentCategoryRead.from_doc(r) for r in rows]


async def upsert_mandatory_rule(scope: AccessScope, payload: MandatoryRuleUpsert) -> dict:
    authorize_hr_document_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    doc = await HrMandatoryDocumentRule.find_one(Eq(HrMandatoryDocumentRule.tenant_id, tenant_id), Eq(HrMandatoryDocumentRule.rule_code, payload.rule_code))
    if doc:
        doc.category_code = payload.category_code
        doc.employment_category_code = payload.employment_category_code
        doc.employment_type_code = payload.employment_type_code
        doc.employment_stage = payload.employment_stage
        doc.is_mandatory = payload.is_mandatory
        doc.updated_by = scope.user_id
        await doc.save()
    else:
        await HrMandatoryDocumentRule(
            tenant_id=tenant_id,
            rule_code=payload.rule_code,
            category_code=payload.category_code,
            employment_category_code=payload.employment_category_code,
            employment_type_code=payload.employment_type_code,
            employment_stage=payload.employment_stage,
            is_mandatory=payload.is_mandatory,
            updated_by=scope.user_id,
        ).insert()
    return {"rule_code": payload.rule_code}


async def upsert_expiry_policy(scope: AccessScope, payload: ExpiryPolicyUpsert) -> dict:
    authorize_hr_document_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    row = await HrDocumentExpiryPolicy.find_one(Eq(HrDocumentExpiryPolicy.tenant_id, tenant_id))
    if row is None:
        row = HrDocumentExpiryPolicy(tenant_id=tenant_id, reminder_days=payload.reminder_days, updated_by=scope.user_id)
        await row.insert()
    else:
        row.reminder_days = payload.reminder_days
        row.updated_by = scope.user_id
        row.updated_at = utcnow()
        await row.save()
    return {"reminder_days": row.reminder_days}


async def _assert_employee_access(scope: AccessScope, tenant_id: PydanticObjectId, employee_user_id: PydanticObjectId, user: User | None) -> None:
    if Permission.HR_DOCUMENT_MANAGE in scope.effective_permissions or Permission.HR_EMPLOYEE_MANAGE in scope.effective_permissions:
        return
    if user and user.id == employee_user_id:
        authorize_hr_portal(scope)
        return
    authorize_hr_document_manage(scope)


async def upload_employee_document(
    scope: AccessScope,
    user: User,
    meta: DocumentUploadMeta,
    upload: UploadFile,
) -> EmployeeDocumentRead:
    tenant_id = require_hr_tenant_scope(scope)
    uid = to_object_id(meta.employee_user_id, "employee_user_id")
    await _assert_employee_access(scope, tenant_id, uid, user)
    employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, uid))
    if employee is None:
        raise AppError(code="NOT_FOUND", message="Employee not found", status_code=404)
    await _seed_categories(tenant_id)
    category = await HrDocumentCategory.find_one(Eq(HrDocumentCategory.tenant_id, tenant_id), Eq(HrDocumentCategory.category_code, meta.category_code))
    if category is None or not category.is_active:
        raise AppError(code="VALIDATION_ERROR", message="Invalid document category", status_code=422)
    raw = await upload.read()
    if not raw:
        raise AppError(code="VALIDATION_ERROR", message="Empty file", status_code=422)
    mime = upload.content_type or "application/octet-stream"
    file_storage.validate_upload(upload.filename or "document.bin", mime, len(raw))
    key = file_storage.storage_key_for(str(tenant_id), "hr_documents", upload.filename or "document.bin")
    file_storage.write_bytes(key, raw)
    doc_code = (meta.document_code or f"{meta.category_code}-{uuid4().hex[:8]}").upper()
    status = HrEmployeeDocumentStatus.PENDING_VERIFICATION if meta.submit_for_verification else HrEmployeeDocumentStatus.DRAFT
    prev_id = to_object_id(meta.replace_document_id, "replace_document_id") if meta.replace_document_id else None
    if prev_id:
        old = await HrEmployeeDocument.get(prev_id)
        if old is None or old.tenant_id != tenant_id or old.employee_user_id != uid:
            raise AppError(code="NOT_FOUND", message="Document to replace not found", status_code=404)
        old.status = HrEmployeeDocumentStatus.REPLACED
        old.replaced_by_document_id = None
        old.updated_at = utcnow()
        await old.save()
        await _log_doc_event(tenant_id, old, "replaced", status_from=old.status.value, status_to=HrEmployeeDocumentStatus.REPLACED.value, note=None, actor_id=scope.user_id)
    row = HrEmployeeDocument(
        tenant_id=tenant_id,
        employee_user_id=uid,
        category_code=meta.category_code,
        document_code=doc_code,
        title=meta.title,
        storage_key=key,
        file_name=upload.filename or "document.bin",
        mime_type=mime,
        file_size=len(raw),
        issue_date=meta.issue_date,
        expires_on=meta.expires_on,
        issuing_authority=meta.issuing_authority,
        remarks=meta.remarks,
        status=status,
        previous_document_id=prev_id,
        submitted_by=scope.user_id,
        submitted_at=utcnow() if meta.submit_for_verification else None,
        actor_id=scope.user_id,
    )
    await row.insert()
    if prev_id:
        old = await HrEmployeeDocument.get(prev_id)
        if old:
            old.replaced_by_document_id = row.id
            await old.save()
    await _log_doc_event(tenant_id, row, "uploaded", status_from=None, status_to=status.value, note=meta.remarks, actor_id=scope.user_id)
    return EmployeeDocumentRead.from_doc(row)


async def submit_document(scope: AccessScope, document_id: str) -> EmployeeDocumentRead:
    authorize_hr_document_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    doc = await HrEmployeeDocument.get(to_object_id(document_id, "document_id"))
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Document not found", status_code=404)
    if doc.status not in {HrEmployeeDocumentStatus.DRAFT, HrEmployeeDocumentStatus.REJECTED}:
        raise AppError(code="CONFLICT", message="Document cannot be submitted", status_code=409)
    prev = doc.status.value
    doc.status = HrEmployeeDocumentStatus.PENDING_VERIFICATION
    doc.submitted_at = utcnow()
    doc.submitted_by = scope.user_id
    doc.updated_at = utcnow()
    await doc.save()
    await _log_doc_event(tenant_id, doc, "submitted", status_from=prev, status_to=doc.status.value, note=None, actor_id=scope.user_id)
    return EmployeeDocumentRead.from_doc(doc)


async def verify_document(scope: AccessScope, document_id: str, payload: DocumentVerificationDecision) -> EmployeeDocumentRead:
    authorize_hr_document_verify(scope)
    tenant_id = require_hr_tenant_scope(scope)
    doc = await HrEmployeeDocument.get(to_object_id(document_id, "document_id"))
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Document not found", status_code=404)
    if doc.status != HrEmployeeDocumentStatus.PENDING_VERIFICATION:
        raise AppError(code="CONFLICT", message="Document is not pending verification", status_code=409)
    if payload.decision not in {HrEmployeeDocumentStatus.VERIFIED, HrEmployeeDocumentStatus.REJECTED}:
        raise AppError(code="VALIDATION_ERROR", message="Invalid verification decision", status_code=422)
    if payload.decision == HrEmployeeDocumentStatus.REJECTED and not payload.reason:
        raise AppError(code="VALIDATION_ERROR", message="Rejection reason is required", status_code=422)
    prev = doc.status.value
    doc.status = payload.decision
    doc.rejection_reason = payload.reason
    doc.verified_by = scope.user_id
    doc.verified_at = utcnow()
    doc.updated_at = utcnow()
    await doc.save()
    await _log_doc_event(tenant_id, doc, "verified", status_from=prev, status_to=doc.status.value, note=payload.reason, actor_id=scope.user_id)
    return EmployeeDocumentRead.from_doc(doc)


async def list_employee_documents(scope: AccessScope, employee_user_id: str, pagination: Pagination) -> Page[EmployeeDocumentRead]:
    authorize_hr_document_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    uid = to_object_id(employee_user_id, "employee_user_id")
    active_statuses = [
        HrEmployeeDocumentStatus.DRAFT,
        HrEmployeeDocumentStatus.SUBMITTED,
        HrEmployeeDocumentStatus.PENDING_VERIFICATION,
        HrEmployeeDocumentStatus.VERIFIED,
        HrEmployeeDocumentStatus.REJECTED,
        HrEmployeeDocumentStatus.EXPIRED,
    ]
    query = HrEmployeeDocument.find(
        Eq(HrEmployeeDocument.tenant_id, tenant_id),
        Eq(HrEmployeeDocument.employee_user_id, uid),
        In(HrEmployeeDocument.status, active_statuses),
    )
    total = await query.count()
    rows = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[EmployeeDocumentRead.from_doc(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def employee_document_overview(scope: AccessScope, employee_user_id: str) -> EmployeeDocumentOverview:
    authorize_hr_document_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    uid = to_object_id(employee_user_id, "employee_user_id")
    policy = await HrDocumentExpiryPolicy.find_one(Eq(HrDocumentExpiryPolicy.tenant_id, tenant_id))
    reminder_days = policy.reminder_days if policy else 30
    today = date.today()
    soon = today + timedelta(days=reminder_days)
    docs = await HrEmployeeDocument.find(Eq(HrEmployeeDocument.tenant_id, tenant_id), Eq(HrEmployeeDocument.employee_user_id, uid)).to_list()
    overview = EmployeeDocumentOverview(total=len(docs))
    for doc in docs:
        overview.by_category[doc.category_code] = overview.by_category.get(doc.category_code, 0) + 1
        if doc.status == HrEmployeeDocumentStatus.VERIFIED:
            overview.verified += 1
        elif doc.status == HrEmployeeDocumentStatus.PENDING_VERIFICATION:
            overview.pending_verification += 1
        elif doc.status == HrEmployeeDocumentStatus.REJECTED:
            overview.rejected += 1
        if doc.status != HrEmployeeDocumentStatus.DRAFT:
            overview.submitted += 1
        if doc.expires_on and doc.expires_on < today:
            overview.expired += 1
        elif doc.expires_on and today <= doc.expires_on <= soon:
            overview.expiring_soon += 1
    mandatory = await mandatory_status_for_employee(scope, employee_user_id)
    overview.missing_mandatory = sum(1 for m in mandatory if not m.submitted)
    return overview


async def mandatory_status_for_employee(scope: AccessScope, employee_user_id: str) -> list[MandatoryDocumentStatus]:
    authorize_hr_document_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    uid = to_object_id(employee_user_id, "employee_user_id")
    profile = await HrEmployeeProfile.find_one(Eq(HrEmployeeProfile.tenant_id, tenant_id), Eq(HrEmployeeProfile.user_id, uid))
    employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, uid))
    rules = await HrMandatoryDocumentRule.find(Eq(HrMandatoryDocumentRule.tenant_id, tenant_id), Eq(HrMandatoryDocumentRule.is_active, True)).to_list()
    if not rules:
        await _seed_categories(tenant_id)
        rules = [
            type("Rule", (), {"rule_code": "DEFAULT_GOV_ID", "category_code": "GOV_ID", "employment_category_code": None, "employment_type_code": None, "is_mandatory": True})(),
            type("Rule", (), {"rule_code": "DEFAULT_ADDRESS", "category_code": "ADDRESS_PROOF", "employment_category_code": None, "employment_type_code": None, "is_mandatory": True})(),
        ]
    docs = await HrEmployeeDocument.find(Eq(HrEmployeeDocument.tenant_id, tenant_id), Eq(HrEmployeeDocument.employee_user_id, uid)).to_list()
    items: list[MandatoryDocumentStatus] = []
    for rule in rules:
        if rule.employment_category_code and profile and profile.employee_category != rule.employment_category_code:
            continue
        if rule.employment_type_code and employee and employee.employment_type != rule.employment_type_code:
            continue
        match = next(
            (
                d
                for d in docs
                if d.category_code == rule.category_code
                and d.status in {HrEmployeeDocumentStatus.VERIFIED, HrEmployeeDocumentStatus.PENDING_VERIFICATION, HrEmployeeDocumentStatus.SUBMITTED}
            ),
            None,
        )
        items.append(
            MandatoryDocumentStatus(
                category_code=rule.category_code,
                rule_code=rule.rule_code,
                submitted=match is not None,
                document_id=str(match.id) if match else None,
                status=match.status.value if match else None,
                expires_on=match.expires_on if match else None,
            )
        )
    return items


async def document_history(scope: AccessScope, document_id: str) -> list[DocumentEventRead]:
    authorize_hr_document_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    doc_id = to_object_id(document_id, "document_id")
    doc = await HrEmployeeDocument.get(doc_id)
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Document not found", status_code=404)
    events = await HrEmployeeDocumentEvent.find(
        Eq(HrEmployeeDocumentEvent.tenant_id, tenant_id),
        Eq(HrEmployeeDocumentEvent.document_id, doc_id),
    ).sort("-created_at").to_list()
    chain: list[DocumentEventRead] = [
        DocumentEventRead(
            event_type=e.event_type,
            status_from=e.status_from,
            status_to=e.status_to,
            note=e.note,
            actor_id=str(e.actor_id) if e.actor_id else None,
            created_at=e.created_at,
        )
        for e in events
    ]
    if doc.previous_document_id:
        prev_events = await HrEmployeeDocumentEvent.find(
            Eq(HrEmployeeDocumentEvent.tenant_id, tenant_id),
            Eq(HrEmployeeDocumentEvent.document_id, doc.previous_document_id),
        ).sort("-created_at").to_list()
        chain.extend(
            DocumentEventRead(
                event_type=f"predecessor:{e.event_type}",
                status_from=e.status_from,
                status_to=e.status_to,
                note=e.note,
                actor_id=str(e.actor_id) if e.actor_id else None,
                created_at=e.created_at,
            )
            for e in prev_events
        )
    return sorted(chain, key=lambda c: c.created_at, reverse=True)


async def download_employee_document(scope: AccessScope, document_id: str, user: User) -> tuple[bytes, str, str]:
    authorize_hr_document_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    doc = await HrEmployeeDocument.get(to_object_id(document_id, "document_id"))
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Document not found", status_code=404)
    await _assert_employee_access(scope, tenant_id, doc.employee_user_id, user)
    if not doc.storage_key.startswith(f"{tenant_id}/"):
        raise AppError(code="FORBIDDEN", message="Invalid document storage", status_code=403)
    data = file_storage.read_bytes(doc.storage_key)
    return data, doc.mime_type, doc.file_name