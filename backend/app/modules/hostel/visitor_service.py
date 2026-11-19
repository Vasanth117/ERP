"""Hostel visitor registration and movement tracking."""

from datetime import datetime, timezone
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.hostel_admin_models import HostelVisitorLog
from app.modules.college_admin.models import InstitutionSettings
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.hostel.policy import authorize_hostel_visitor_manage, authorize_hostel_visitor_read, require_hostel_tenant_scope
from app.modules.hostel.resident_models import HostelResident as PortalResident
from app.modules.hostel.resident_models import HostelResidentStatus
from app.modules.hostel.visitor_models import (
    HostelVisitorActivityHistory,
    HostelVisitorApproval,
    HostelVisitorEntry,
    HostelVisitorProfile,
    HostelVisitorRestriction,
    HostelVisitorStatus,
)
from app.modules.hostel.visitor_schemas import (
    VisitorApprovalInput,
    VisitorDenyInput,
    VisitorEntryInput,
    VisitorEntryRead,
    VisitorExitInput,
    VisitorRegisterInput,
    VisitorRestrictionUpsert,
)


async def _visitor_policy(tenant_id: PydanticObjectId, hostel_code: str | None) -> HostelVisitorRestriction | None:
    code = hostel_code.upper() if hostel_code else None
    return await HostelVisitorRestriction.find_one({"tenant_id": tenant_id, "hostel_code": code})


async def _activity(tenant_id: PydanticObjectId, visit_id: str, event_type: str, actor_id, note=None):
    await HostelVisitorActivityHistory(
        tenant_id=tenant_id,
        visit_id=visit_id,
        event_type=event_type,
        note=note,
        actor_id=actor_id,
    ).insert()


def _entry_read(doc: HostelVisitorEntry) -> VisitorEntryRead:
    return VisitorEntryRead(
        visit_id=doc.visit_id,
        visitor_name=doc.visitor_name,
        resident_user_id=str(doc.resident_user_id),
        hostel_code=doc.hostel_code,
        status=doc.status,
        purpose=doc.purpose,
        expected_arrival=doc.expected_arrival,
        expected_departure=doc.expected_departure,
        actual_entry_at=doc.actual_entry_at,
        actual_exit_at=doc.actual_exit_at,
        created_at=doc.created_at,
    )


async def register_visitor(scope: AccessScope, payload: VisitorRegisterInput) -> VisitorEntryRead:
    authorize_hostel_visitor_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    resident_id = to_object_id(payload.resident_user_id, "resident_user_id")
    resident = await PortalResident.find_one(
        Eq(PortalResident.tenant_id, tenant_id),
        Eq(PortalResident.student_user_id, resident_id),
        Eq(PortalResident.status, HostelResidentStatus.CHECKED_IN),
    )
    if resident is None:
        raise AppError(code="VALIDATION_ERROR", message="Resident must be checked in", status_code=422)
    hostel_code = (payload.hostel_code or resident.hostel_code or "").upper() or None
    policy = await _visitor_policy(tenant_id, hostel_code)
    if policy and policy.max_visitors_per_resident is not None:
        inside = await HostelVisitorEntry.find(
            {
                "tenant_id": tenant_id,
                "resident_user_id": resident_id,
                "status": {"$in": [HostelVisitorStatus.INSIDE.value, HostelVisitorStatus.ENTRY_RECORDED.value]},
            }
        ).count()
        if inside >= policy.max_visitors_per_resident:
            raise AppError(code="CONFLICT", message="Visitor limit for resident reached", status_code=409)
    settings = await InstitutionSettings.find_one(Eq(InstitutionSettings.tenant_id, tenant_id))
    visitor_cfg = (settings.settings.get("hostel") or {}).get("visitor_policy", {}) if settings else {}
    approval_required = payload.approval_required if payload.approval_required is not None else visitor_cfg.get("default_approval_required", False)
    visit_id = f"hvis_{uuid4().hex[:10]}"
    status = HostelVisitorStatus.AWAITING_APPROVAL if approval_required else HostelVisitorStatus.APPROVED
    if payload.walk_in and not approval_required:
        status = HostelVisitorStatus.APPROVED
    if not payload.walk_in:
        status = HostelVisitorStatus.EXPECTED
    doc = HostelVisitorEntry(
        tenant_id=tenant_id,
        visit_id=visit_id,
        resident_user_id=resident_id,
        hostel_code=hostel_code,
        visitor_name=payload.visitor_name.strip(),
        mobile_number=payload.mobile_number,
        id_type=payload.id_type,
        id_reference=payload.id_reference,
        photo_ref=payload.photo_ref,
        visitor_address=payload.visitor_address,
        organization=payload.organization,
        purpose=payload.purpose.strip(),
        relationship_to_resident=payload.relationship_to_resident,
        accompanying_count=payload.accompanying_count,
        expected_arrival=payload.expected_arrival,
        expected_departure=payload.expected_departure,
        vehicle_info=payload.vehicle_info,
        remarks=payload.remarks,
        approval_required=approval_required,
        status=status,
        actor_id=scope.user_id,
    )
    await doc.insert()
    await _activity(tenant_id, visit_id, "registered", scope.user_id)
    return _entry_read(doc)


async def approve_visitor(scope: AccessScope, payload: VisitorApprovalInput) -> VisitorEntryRead:
    authorize_hostel_visitor_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    doc = await HostelVisitorEntry.find_one(Eq(HostelVisitorEntry.tenant_id, tenant_id), Eq(HostelVisitorEntry.visit_id, payload.visit_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Visit not found", status_code=404)
    if doc.status not in (HostelVisitorStatus.AWAITING_APPROVAL, HostelVisitorStatus.EXPECTED):
        raise AppError(code="CONFLICT", message="Visit not pending approval", status_code=409)
    await HostelVisitorApproval(
        tenant_id=tenant_id,
        approval_id=f"hva_{uuid4().hex[:8]}",
        visit_id=doc.visit_id,
        approver_role=payload.approver_role,
        decision="approved" if payload.approved else "rejected",
        remarks=payload.remarks,
        actor_id=scope.user_id,
    ).insert()
    doc.status = HostelVisitorStatus.APPROVED if payload.approved else HostelVisitorStatus.REJECTED
    doc.approver_id = scope.user_id
    doc.denied_reason = payload.remarks if not payload.approved else None
    doc.updated_at = utcnow()
    await doc.save()
    await _activity(tenant_id, doc.visit_id, "approval_decision", scope.user_id, payload.remarks)
    return _entry_read(doc)


async def record_visitor_entry(scope: AccessScope, payload: VisitorEntryInput) -> VisitorEntryRead:
    authorize_hostel_visitor_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    doc = await HostelVisitorEntry.find_one(Eq(HostelVisitorEntry.tenant_id, tenant_id), Eq(HostelVisitorEntry.visit_id, payload.visit_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Visit not found", status_code=404)
    if doc.status in (HostelVisitorStatus.INSIDE, HostelVisitorStatus.EXITED, HostelVisitorStatus.REJECTED, HostelVisitorStatus.CANCELLED):
        raise AppError(code="CONFLICT", message="Visit cannot record entry", status_code=409)
    if doc.approval_required and doc.status != HostelVisitorStatus.APPROVED:
        raise AppError(code="CONFLICT", message="Visit not approved", status_code=409)
    profile = None
    if doc.mobile_number:
        profile = await HostelVisitorProfile.find_one({"tenant_id": tenant_id, "mobile_number": doc.mobile_number, "blacklisted": True})
    if profile:
        raise AppError(code="FORBIDDEN", message="Visitor is restricted", status_code=403)
    now = utcnow()
    doc.status = HostelVisitorStatus.INSIDE
    doc.actual_entry_at = now
    doc.pass_reference = payload.pass_reference or f"PASS-{doc.visit_id[-6:].upper()}"
    doc.updated_at = now
    await doc.save()
    await HostelVisitorLog(
        tenant_id=tenant_id,
        visit_id=doc.visit_id,
        resident_user_id=doc.resident_user_id,
        visitor_name=doc.visitor_name,
        purpose=doc.purpose,
        check_in_at=now,
        actor_id=scope.user_id,
    ).insert()
    await _activity(tenant_id, doc.visit_id, "entry_recorded", scope.user_id)
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="hostel.visitor.entry",
        module="hostel",
        resource_type="hostel_visitor_entry",
        resource_id=doc.visit_id,
    )
    return _entry_read(doc)


async def record_visitor_exit(scope: AccessScope, payload: VisitorExitInput) -> VisitorEntryRead:
    authorize_hostel_visitor_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    doc = await HostelVisitorEntry.find_one(Eq(HostelVisitorEntry.tenant_id, tenant_id), Eq(HostelVisitorEntry.visit_id, payload.visit_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Visit not found", status_code=404)
    if doc.status != HostelVisitorStatus.INSIDE:
        raise AppError(code="CONFLICT", message="Visitor is not inside", status_code=409)
    if doc.actual_exit_at is not None:
        raise AppError(code="CONFLICT", message="Visitor already checked out", status_code=409)
    now = utcnow()
    doc.status = HostelVisitorStatus.EXITED
    doc.actual_exit_at = now
    doc.updated_at = now
    await doc.save()
    legacy = await HostelVisitorLog.find_one(Eq(HostelVisitorLog.tenant_id, tenant_id), Eq(HostelVisitorLog.visit_id, doc.visit_id))
    if legacy:
        legacy.check_out_at = now
        await legacy.save()
    await _activity(tenant_id, doc.visit_id, "exit_recorded", scope.user_id, payload.note)
    return _entry_read(doc)


async def deny_visitor_entry(scope: AccessScope, payload: VisitorDenyInput) -> VisitorEntryRead:
    authorize_hostel_visitor_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    doc = await HostelVisitorEntry.find_one(Eq(HostelVisitorEntry.tenant_id, tenant_id), Eq(HostelVisitorEntry.visit_id, payload.visit_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Visit not found", status_code=404)
    doc.status = HostelVisitorStatus.REJECTED
    doc.denied_reason = payload.reason
    doc.updated_at = utcnow()
    await doc.save()
    await _activity(tenant_id, doc.visit_id, "denied", scope.user_id, payload.reason)
    return _entry_read(doc)


async def list_visitors(
    scope: AccessScope,
    pagination: Pagination,
    *,
    status: HostelVisitorStatus | None = None,
    hostel_code: str | None = None,
    resident_user_id: str | None = None,
) -> Page[VisitorEntryRead]:
    authorize_hostel_visitor_read(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    query: dict = {"tenant_id": tenant_id}
    if status:
        query["status"] = status.value
    if hostel_code:
        query["hostel_code"] = hostel_code.upper()
    if resident_user_id:
        query["resident_user_id"] = to_object_id(resident_user_id, "resident_user_id")
    total = await HostelVisitorEntry.find(query).count()
    rows = await HostelVisitorEntry.find(query).sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[_entry_read(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def visitors_inside(scope: AccessScope, pagination: Pagination) -> Page[VisitorEntryRead]:
    return await list_visitors(scope, pagination, status=HostelVisitorStatus.INSIDE)


async def visitor_daily_report(scope: AccessScope, anchor: datetime | None = None) -> dict:
    authorize_hostel_visitor_read(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    day = anchor or datetime.now(timezone.utc)
    start = datetime.combine(day.date(), datetime.min.time(), tzinfo=timezone.utc)
    end = datetime.combine(day.date(), datetime.max.time(), tzinfo=timezone.utc)
    entries = await HostelVisitorEntry.find({"tenant_id": tenant_id, "actual_entry_at": {"$gte": start, "$lte": end}}).count()
    inside = await HostelVisitorEntry.find({"tenant_id": tenant_id, "status": HostelVisitorStatus.INSIDE.value}).count()
    rejected = await HostelVisitorEntry.find({"tenant_id": tenant_id, "status": HostelVisitorStatus.REJECTED.value, "updated_at": {"$gte": start}}).count()
    overdue = await mark_overdue_visitors(tenant_id)
    return {"date": day.date().isoformat(), "entries_today": entries, "currently_inside": inside, "rejected_today": rejected, "marked_overdue": overdue}


async def mark_overdue_visitors(tenant_id: PydanticObjectId) -> int:
    now = utcnow()
    rows = await HostelVisitorEntry.find(
        {
            "tenant_id": tenant_id,
            "status": HostelVisitorStatus.INSIDE.value,
            "expected_departure": {"$lt": now},
        }
    ).to_list()
    for doc in rows:
        doc.status = HostelVisitorStatus.OVERDUE
        doc.updated_at = now
        await doc.save()
        await _activity(tenant_id, doc.visit_id, "overdue", None)
    return len(rows)


async def upsert_visitor_restrictions(scope: AccessScope, payload: VisitorRestrictionUpsert) -> dict:
    authorize_hostel_visitor_manage(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    code = payload.hostel_code.upper() if payload.hostel_code else None
    doc = await HostelVisitorRestriction.find_one({"tenant_id": tenant_id, "hostel_code": code})
    if doc:
        doc.visiting_hours = payload.visiting_hours
        doc.max_visitors_per_resident = payload.max_visitors_per_resident
        doc.allowed_weekdays = payload.allowed_weekdays
        doc.restricted_visitor_types = payload.restricted_visitor_types
        doc.policy_notes = payload.policy_notes
        doc.updated_at = utcnow()
        await doc.save()
    else:
        await HostelVisitorRestriction(
            tenant_id=tenant_id,
            hostel_code=code,
            visiting_hours=payload.visiting_hours,
            max_visitors_per_resident=payload.max_visitors_per_resident,
            allowed_weekdays=payload.allowed_weekdays,
            restricted_visitor_types=payload.restricted_visitor_types,
            policy_notes=payload.policy_notes,
        ).insert()
    return {"hostel_code": code, "updated": True}