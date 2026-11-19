"""Institution helpdesk and support."""

import base64
from datetime import datetime, timedelta
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.helpdesk_admin_models import (
    InstitutionSupportAssignment,
    InstitutionSupportAttachment,
    InstitutionSupportCategory,
    InstitutionSupportComment,
    InstitutionSupportEscalation,
    InstitutionSupportFeedback,
    InstitutionSupportHistory,
    InstitutionSupportInternalNote,
    InstitutionSupportSlaPolicy,
    InstitutionSupportTicket,
    RequesterAudience,
    SupportPriority,
    SupportTicketStatus,
)
from app.modules.college_admin.helpdesk_admin_schemas import (
    SupportAssignRequest,
    SupportAttachmentCreate,
    SupportCategoryRead,
    SupportCommentCreate,
    SupportEscalateRequest,
    SupportHistoryItem,
    SupportInternalNoteCreate,
    SupportPerformanceReport,
    SupportReopenRequest,
    SupportResolveRequest,
    SupportSlaStatus,
    SupportTicketCreate,
    SupportTicketRead,
    SupportTicketUpdate,
)
from app.modules.college_admin.import_file_utils import file_checksum, validate_import_file, write_import_file
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.messaging.outbox_models import DomainOutboxEvent, OutboxEventStatus

OPEN_STATUSES = frozenset(
    {
        SupportTicketStatus.OPEN,
        SupportTicketStatus.ASSIGNED,
        SupportTicketStatus.IN_PROGRESS,
        SupportTicketStatus.WAITING_FOR_INFORMATION,
        SupportTicketStatus.ESCALATED,
        SupportTicketStatus.REOPENED,
    }
)

STATUS_TRANSITIONS: dict[SupportTicketStatus, frozenset[SupportTicketStatus]] = {
    SupportTicketStatus.OPEN: frozenset({SupportTicketStatus.ASSIGNED, SupportTicketStatus.IN_PROGRESS, SupportTicketStatus.CLOSED}),
    SupportTicketStatus.ASSIGNED: frozenset({SupportTicketStatus.IN_PROGRESS, SupportTicketStatus.WAITING_FOR_INFORMATION}),
    SupportTicketStatus.IN_PROGRESS: frozenset({SupportTicketStatus.WAITING_FOR_INFORMATION, SupportTicketStatus.RESOLVED}),
    SupportTicketStatus.WAITING_FOR_INFORMATION: frozenset({SupportTicketStatus.IN_PROGRESS, SupportTicketStatus.RESOLVED}),
    SupportTicketStatus.ESCALATED: frozenset({SupportTicketStatus.IN_PROGRESS, SupportTicketStatus.ASSIGNED}),
    SupportTicketStatus.RESOLVED: frozenset({SupportTicketStatus.CLOSED, SupportTicketStatus.REOPENED}),
    SupportTicketStatus.REOPENED: frozenset({SupportTicketStatus.IN_PROGRESS, SupportTicketStatus.ASSIGNED}),
    SupportTicketStatus.CLOSED: frozenset({SupportTicketStatus.REOPENED}),
}

_DEFAULT_CATEGORIES = [
    {"code": "academic", "title": "Academic", "module": "academics", "issue": "general"},
    {"code": "finance", "title": "Finance", "module": "finance", "issue": "billing"},
    {"code": "hr", "title": "HR", "module": "hr", "issue": "general"},
    {"code": "it", "title": "IT", "module": "platform", "issue": "access"},
    {"code": "hostel", "title": "Hostel", "module": "hostel", "issue": "allocation"},
]


def _can_manage(scope: AccessScope) -> bool:
    try:
        authorize(scope, Permission.HELPDESK_ADMIN_MANAGE)
        return True
    except AppError:
        return False


def _can_internal(scope: AccessScope) -> bool:
    try:
        authorize(scope, Permission.HELPDESK_ADMIN_INTERNAL)
        return True
    except AppError:
        return _can_manage(scope)


def _aware(dt: datetime | None, ref: datetime) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=ref.tzinfo)
    return dt


def _is_overdue(ticket: InstitutionSupportTicket) -> bool:
    now = utcnow()
    if ticket.status in {SupportTicketStatus.RESOLVED, SupportTicketStatus.CLOSED}:
        return False
    due = _aware(ticket.resolution_due_at, now)
    if due and due < now:
        return True
    first = _aware(ticket.first_response_due_at, now)
    if first and first < now and ticket.status == SupportTicketStatus.OPEN:
        return True
    return False


async def _sla_policy(tenant_id: PydanticObjectId) -> InstitutionSupportSlaPolicy:
    doc = await InstitutionSupportSlaPolicy.find_one(
        Eq(InstitutionSupportSlaPolicy.tenant_id, tenant_id),
        Eq(InstitutionSupportSlaPolicy.policy_id, "default"),
    )
    if doc is None:
        doc = InstitutionSupportSlaPolicy(tenant_id=tenant_id)
        await doc.insert()
    return doc


async def _ensure_categories(tenant_id: PydanticObjectId) -> None:
    for item in _DEFAULT_CATEGORIES:
        exists = await InstitutionSupportCategory.find_one(
            Eq(InstitutionSupportCategory.tenant_id, tenant_id),
            Eq(InstitutionSupportCategory.category_code, item["code"]),
        )
        if exists:
            continue
        await InstitutionSupportCategory(
            tenant_id=tenant_id,
            category_code=item["code"],
            title=item["title"],
            module_key=item["module"],
            issue_type=item["issue"],
        ).insert()


async def _history(tenant_id: PydanticObjectId, ticket_id: str, change_type: str, actor_id: PydanticObjectId | None, summary: str, metadata: dict | None = None) -> None:
    await InstitutionSupportHistory(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        change_type=change_type,
        actor_id=actor_id,
        summary=summary,
        metadata=metadata or {},
    ).insert()


async def _notify(tenant_id: PydanticObjectId, ticket_id: str, event_type: str, payload: dict) -> None:
    key = f"helpdesk:{ticket_id}:{event_type}:{uuid4().hex[:8]}"
    if await DomainOutboxEvent.find_one(Eq(DomainOutboxEvent.tenant_id, tenant_id), Eq(DomainOutboxEvent.idempotency_key, key)):
        return
    await DomainOutboxEvent(
        tenant_id=tenant_id,
        event_type=event_type,
        aggregate_type="institution_support_ticket",
        aggregate_id=ticket_id,
        payload=payload,
        idempotency_key=key,
        status=OutboxEventStatus.PENDING,
    ).insert()


def _ticket_read(ticket: InstitutionSupportTicket) -> SupportTicketRead:
    return SupportTicketRead(
        ticket_id=ticket.ticket_id,
        ticket_number=ticket.ticket_number,
        title=ticket.title,
        description=ticket.description,
        category_code=ticket.category_code,
        module_key=ticket.module_key,
        issue_type=ticket.issue_type,
        priority=ticket.priority,
        status=ticket.status,
        requester_user_id=str(ticket.requester_user_id),
        requester_audience=ticket.requester_audience,
        assigned_user_id=str(ticket.assigned_user_id) if ticket.assigned_user_id else None,
        assigned_team=ticket.assigned_team,
        first_response_due_at=ticket.first_response_due_at,
        resolution_due_at=ticket.resolution_due_at,
        is_overdue=_is_overdue(ticket),
        resolved_at=ticket.resolved_at,
        resolution_detail=ticket.resolution_detail,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )


async def _assert_ticket_access(scope: AccessScope, ticket: InstitutionSupportTicket, *, write: bool = False) -> None:
    if _can_manage(scope):
        return
    if scope.user_id == ticket.requester_user_id:
        if write and ticket.status in {SupportTicketStatus.RESOLVED, SupportTicketStatus.CLOSED}:
            raise AppError(code="FORBIDDEN", message="Cannot modify closed ticket", status_code=403)
        return
    if ticket.assigned_user_id and scope.user_id == ticket.assigned_user_id and not write:
        return
    authorize(scope, Permission.HELPDESK_ADMIN_READ)


async def _get_ticket(tenant_id: PydanticObjectId, ticket_id: str) -> InstitutionSupportTicket:
    doc = await InstitutionSupportTicket.find_one(
        Eq(InstitutionSupportTicket.tenant_id, tenant_id),
        Eq(InstitutionSupportTicket.ticket_id, ticket_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Ticket not found", status_code=404)
    return doc


async def list_categories(scope: AccessScope) -> list[SupportCategoryRead]:
    authorize(scope, Permission.HELPDESK_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    await _ensure_categories(tenant_id)
    docs = await InstitutionSupportCategory.find(Eq(InstitutionSupportCategory.tenant_id, tenant_id), Eq(InstitutionSupportCategory.active, True)).to_list()
    return [
        SupportCategoryRead(category_code=d.category_code, title=d.title, module_key=d.module_key, issue_type=d.issue_type)
        for d in docs
    ]


async def create_ticket(scope: AccessScope, user: User, payload: SupportTicketCreate) -> SupportTicketRead:
    authorize(scope, Permission.HELPDESK_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    await _ensure_categories(tenant_id)
    cat = await InstitutionSupportCategory.find_one(
        Eq(InstitutionSupportCategory.tenant_id, tenant_id),
        Eq(InstitutionSupportCategory.category_code, payload.category_code),
    )
    if cat is None:
        raise AppError(code="VALIDATION_ERROR", message="Invalid category", status_code=422)
    if payload.idempotency_key:
        existing = await InstitutionSupportTicket.find_one(
            Eq(InstitutionSupportTicket.tenant_id, tenant_id),
            Eq(InstitutionSupportTicket.idempotency_key, payload.idempotency_key),
        )
        if existing:
            return _ticket_read(existing)
    requester = to_object_id(payload.requester_user_id, "requester_user_id") if payload.requester_user_id else user.id
    requester_user = await User.get(requester)
    if requester_user is None or requester_user.tenant_id != tenant_id:
        raise AppError(code="VALIDATION_ERROR", message="Invalid requester", status_code=422)
    sla = await _sla_policy(tenant_id)
    mult = sla.priority_multipliers.get(payload.priority.value, 1.0)
    now = utcnow()
    ticket_id = f"tkt_{uuid4().hex[:12]}"
    ticket_number = f"IST-{now.strftime('%Y%m')}-{uuid4().hex[:6].upper()}"
    ticket = InstitutionSupportTicket(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        ticket_number=ticket_number,
        title=payload.title,
        description=payload.description,
        category_code=payload.category_code,
        module_key=payload.module_key,
        issue_type=payload.issue_type,
        priority=payload.priority,
        requester_user_id=requester,
        requester_audience=payload.requester_audience,
        first_response_due_at=now + timedelta(hours=sla.first_response_hours * mult),
        resolution_due_at=now + timedelta(hours=sla.resolution_hours * mult),
        idempotency_key=payload.idempotency_key,
    )
    await ticket.insert()
    await _history(tenant_id, ticket_id, "created", user.id, "Ticket created")
    await _notify(tenant_id, ticket_id, "support.ticket.created", {"ticket_id": ticket_id, "requester": str(requester)})
    await append_institution_audit(
        tenant_id,
        actor_id=user.id,
        action="helpdesk.ticket.create",
        module="helpdesk",
        resource_type="support_ticket",
        resource_id=ticket_id,
    )
    return _ticket_read(ticket)


async def list_tickets(scope: AccessScope, pagination: Pagination, *, status: SupportTicketStatus | None = None, assigned_to_me: bool = False) -> Page[SupportTicketRead]:
    authorize(scope, Permission.HELPDESK_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    query = InstitutionSupportTicket.find(Eq(InstitutionSupportTicket.tenant_id, tenant_id))
    if not _can_manage(scope):
        query = query.find(
            {
                "$or": [
                    {"requester_user_id": scope.user_id},
                    {"assigned_user_id": scope.user_id},
                ]
            }
        )
    if status:
        query = query.find(Eq(InstitutionSupportTicket.status, status))
    if assigned_to_me:
        query = query.find(Eq(InstitutionSupportTicket.assigned_user_id, scope.user_id))
    total = await query.count()
    docs = await query.sort("-updated_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[_ticket_read(d) for d in docs], total=total, limit=pagination.limit, offset=pagination.offset)


async def get_ticket_detail(scope: AccessScope, ticket_id: str, *, include_internal: bool = False) -> SupportTicketRead:
    authorize(scope, Permission.HELPDESK_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    ticket = await _get_ticket(tenant_id, ticket_id)
    await _assert_ticket_access(scope, ticket)
    data = _ticket_read(ticket)
    comments = await InstitutionSupportComment.find(
        Eq(InstitutionSupportComment.tenant_id, tenant_id),
        Eq(InstitutionSupportComment.ticket_id, ticket_id),
    ).sort("+created_at").to_list()
    data.comments = [{"comment_id": c.comment_id, "author_id": str(c.author_id), "body": c.body, "created_at": c.created_at.isoformat()} for c in comments]
    attachments = await InstitutionSupportAttachment.find(
        Eq(InstitutionSupportAttachment.tenant_id, tenant_id),
        Eq(InstitutionSupportAttachment.ticket_id, ticket_id),
    ).to_list()
    data.attachments = [{"attachment_id": a.attachment_id, "file_name": a.file_name, "size_bytes": a.size_bytes} for a in attachments]
    if include_internal and _can_internal(scope):
        notes = await InstitutionSupportInternalNote.find(
            Eq(InstitutionSupportInternalNote.tenant_id, tenant_id),
            Eq(InstitutionSupportInternalNote.ticket_id, ticket_id),
        ).sort("-created_at").to_list()
        data.internal_notes = [{"note_id": n.note_id, "author_id": str(n.author_id), "body": n.body, "created_at": n.created_at.isoformat()} for n in notes]
    elif include_internal:
        raise AppError(code="FORBIDDEN", message="Internal notes not permitted", status_code=403)
    return data


async def update_ticket(scope: AccessScope, user: User, ticket_id: str, payload: SupportTicketUpdate) -> SupportTicketRead:
    authorize(scope, Permission.HELPDESK_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    ticket = await _get_ticket(tenant_id, ticket_id)
    if payload.status and payload.status != ticket.status:
        allowed = STATUS_TRANSITIONS.get(ticket.status, frozenset())
        if payload.status not in allowed:
            raise AppError(code="VALIDATION_ERROR", message="Invalid status transition", status_code=422)
        ticket.status = payload.status
        await _history(tenant_id, ticket_id, "status", user.id, f"Status -> {payload.status.value}")
    if payload.priority:
        ticket.priority = payload.priority
    ticket.updated_at = utcnow()
    await ticket.save()
    return _ticket_read(ticket)


async def assign_ticket(scope: AccessScope, user: User, ticket_id: str, payload: SupportAssignRequest) -> SupportTicketRead:
    authorize(scope, Permission.HELPDESK_ADMIN_ASSIGN)
    tenant_id = require_college_tenant_scope(scope)
    ticket = await _get_ticket(tenant_id, ticket_id)
    assignee = to_object_id(payload.assignee_user_id, "assignee_user_id") if payload.assignee_user_id else None
    if assignee:
        assignee_user = await User.get(assignee)
        if assignee_user is None or assignee_user.tenant_id != tenant_id:
            raise AppError(code="VALIDATION_ERROR", message="Invalid assignee", status_code=422)
    await InstitutionSupportAssignment.find(
        Eq(InstitutionSupportAssignment.tenant_id, tenant_id),
        Eq(InstitutionSupportAssignment.ticket_id, ticket_id),
        Eq(InstitutionSupportAssignment.active, True),
    ).update({"$set": {"active": False}})
    aid = f"asg_{uuid4().hex[:10]}"
    await InstitutionSupportAssignment(
        tenant_id=tenant_id,
        assignment_id=aid,
        ticket_id=ticket_id,
        assignee_user_id=assignee,
        assigned_team=payload.assigned_team,
        assigned_by=user.id,
    ).insert()
    ticket.assigned_user_id = assignee
    ticket.assigned_team = payload.assigned_team
    ticket.status = SupportTicketStatus.ASSIGNED if ticket.status == SupportTicketStatus.OPEN else ticket.status
    ticket.updated_at = utcnow()
    await ticket.save()
    await _history(tenant_id, ticket_id, "assignment", user.id, "Ticket reassigned", {"assignment_id": aid})
    await _notify(tenant_id, ticket_id, "support.ticket.assigned", {"assignee": str(assignee) if assignee else None})
    await append_institution_audit(tenant_id, actor_id=user.id, action="helpdesk.assign", module="helpdesk", resource_type="support_ticket", resource_id=ticket_id)
    return _ticket_read(ticket)


async def add_comment(scope: AccessScope, user: User, ticket_id: str, payload: SupportCommentCreate) -> dict:
    authorize(scope, Permission.HELPDESK_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    ticket = await _get_ticket(tenant_id, ticket_id)
    await _assert_ticket_access(scope, ticket, write=True)
    cid = f"cmt_{uuid4().hex[:10]}"
    await InstitutionSupportComment(
        tenant_id=tenant_id,
        comment_id=cid,
        ticket_id=ticket_id,
        author_id=user.id,
        body=payload.body,
    ).insert()
    if ticket.status == SupportTicketStatus.OPEN:
        ticket.status = SupportTicketStatus.IN_PROGRESS
        ticket.updated_at = utcnow()
        await ticket.save()
    await _history(tenant_id, ticket_id, "comment", user.id, "Comment added")
    await _notify(tenant_id, ticket_id, "support.ticket.comment", {"comment_id": cid})
    return {"comment_id": cid}


async def add_internal_note(scope: AccessScope, user: User, ticket_id: str, payload: SupportInternalNoteCreate) -> dict:
    authorize(scope, Permission.HELPDESK_ADMIN_INTERNAL)
    tenant_id = require_college_tenant_scope(scope)
    await _get_ticket(tenant_id, ticket_id)
    nid = f"note_{uuid4().hex[:10]}"
    await InstitutionSupportInternalNote(
        tenant_id=tenant_id,
        note_id=nid,
        ticket_id=ticket_id,
        author_id=user.id,
        body=payload.body,
    ).insert()
    await _history(tenant_id, ticket_id, "internal_note", user.id, "Internal note added")
    return {"note_id": nid}


async def add_attachment(scope: AccessScope, user: User, ticket_id: str, payload: SupportAttachmentCreate) -> dict:
    authorize(scope, Permission.HELPDESK_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    ticket = await _get_ticket(tenant_id, ticket_id)
    await _assert_ticket_access(scope, ticket, write=True)
    raw = base64.b64decode(payload.content_base64, validate=True)
    validate_import_file(payload.file_name, payload.mime_type, len(raw))
    aid = f"att_{uuid4().hex[:10]}"
    storage_key = f"{tenant_id}/helpdesk/{ticket_id}/{aid}_{payload.file_name}"
    write_import_file(storage_key, raw)
    await InstitutionSupportAttachment(
        tenant_id=tenant_id,
        attachment_id=aid,
        ticket_id=ticket_id,
        file_name=payload.file_name,
        mime_type=payload.mime_type,
        storage_key=storage_key,
        size_bytes=len(raw),
        uploaded_by=user.id,
    ).insert()
    await _history(tenant_id, ticket_id, "attachment", user.id, "Attachment uploaded", {"checksum": file_checksum(raw)})
    return {"attachment_id": aid}


async def escalate_ticket(scope: AccessScope, user: User, ticket_id: str, payload: SupportEscalateRequest) -> SupportTicketRead:
    authorize(scope, Permission.HELPDESK_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    ticket = await _get_ticket(tenant_id, ticket_id)
    eid = f"esc_{uuid4().hex[:10]}"
    await InstitutionSupportEscalation(
        tenant_id=tenant_id,
        escalation_id=eid,
        ticket_id=ticket_id,
        reason=payload.reason,
        target_team=payload.target_team,
        escalated_by=user.id,
    ).insert()
    ticket.status = SupportTicketStatus.ESCALATED
    ticket.assigned_team = payload.target_team
    ticket.updated_at = utcnow()
    await ticket.save()
    await _history(tenant_id, ticket_id, "escalation", user.id, payload.reason)
    await _notify(tenant_id, ticket_id, "support.ticket.escalated", {"target_team": payload.target_team})
    await append_institution_audit(tenant_id, actor_id=user.id, action="helpdesk.escalate", module="helpdesk", resource_type="support_ticket", resource_id=ticket_id)
    return _ticket_read(ticket)


async def get_sla_status(scope: AccessScope, ticket_id: str) -> SupportSlaStatus:
    authorize(scope, Permission.HELPDESK_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    ticket = await _get_ticket(tenant_id, ticket_id)
    await _assert_ticket_access(scope, ticket)
    return SupportSlaStatus(
        ticket_id=ticket_id,
        first_response_due_at=ticket.first_response_due_at,
        resolution_due_at=ticket.resolution_due_at,
        is_overdue=_is_overdue(ticket),
    )


async def resolve_ticket(scope: AccessScope, user: User, ticket_id: str, payload: SupportResolveRequest) -> SupportTicketRead:
    authorize(scope, Permission.HELPDESK_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    ticket = await _get_ticket(tenant_id, ticket_id)
    if ticket.status not in OPEN_STATUSES:
        raise AppError(code="VALIDATION_ERROR", message="Ticket is not open", status_code=422)
    ticket.status = SupportTicketStatus.RESOLVED
    ticket.resolved_at = utcnow()
    ticket.resolved_by = user.id
    ticket.resolution_detail = payload.resolution_detail
    ticket.updated_at = utcnow()
    await ticket.save()
    await _history(tenant_id, ticket_id, "resolved", user.id, "Ticket resolved")
    await _notify(tenant_id, ticket_id, "support.ticket.resolved", {})
    return _ticket_read(ticket)


async def reopen_ticket(scope: AccessScope, user: User, ticket_id: str, payload: SupportReopenRequest) -> SupportTicketRead:
    authorize(scope, Permission.HELPDESK_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    ticket = await _get_ticket(tenant_id, ticket_id)
    if ticket.status not in {SupportTicketStatus.RESOLVED, SupportTicketStatus.CLOSED}:
        raise AppError(code="VALIDATION_ERROR", message="Ticket cannot be reopened", status_code=422)
    if ticket.reopen_count >= 3:
        raise AppError(code="FORBIDDEN", message="Maximum reopen limit reached", status_code=403)
    ticket.status = SupportTicketStatus.REOPENED
    ticket.reopen_count += 1
    ticket.resolved_at = None
    ticket.resolved_by = None
    ticket.updated_at = utcnow()
    await ticket.save()
    await _history(tenant_id, ticket_id, "reopened", user.id, payload.reason)
    return _ticket_read(ticket)


async def ticket_history(scope: AccessScope, ticket_id: str) -> list[SupportHistoryItem]:
    authorize(scope, Permission.HELPDESK_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    ticket = await _get_ticket(tenant_id, ticket_id)
    await _assert_ticket_access(scope, ticket)
    rows = await InstitutionSupportHistory.find(
        Eq(InstitutionSupportHistory.tenant_id, tenant_id),
        Eq(InstitutionSupportHistory.ticket_id, ticket_id),
    ).sort("-created_at").to_list()
    return [
        SupportHistoryItem(
            change_type=r.change_type,
            actor_id=str(r.actor_id) if r.actor_id else None,
            summary=r.summary,
            created_at=r.created_at,
        )
        for r in rows
    ]


async def support_performance_report(scope: AccessScope) -> SupportPerformanceReport:
    authorize(scope, Permission.HELPDESK_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    open_count = await InstitutionSupportTicket.find(
        Eq(InstitutionSupportTicket.tenant_id, tenant_id),
        In(InstitutionSupportTicket.status, list(OPEN_STATUSES)),
    ).count()
    all_open = await InstitutionSupportTicket.find(
        Eq(InstitutionSupportTicket.tenant_id, tenant_id),
        In(InstitutionSupportTicket.status, list(OPEN_STATUSES)),
    ).to_list()
    overdue = sum(1 for t in all_open if _is_overdue(t))
    week = utcnow() - timedelta(days=7)
    resolved = await InstitutionSupportTicket.find(
        {
            "tenant_id": tenant_id,
            "status": SupportTicketStatus.RESOLVED,
            "resolved_at": {"$gte": week},
        }
    ).to_list()
    durations = []
    for t in resolved:
        if t.resolved_at:
            durations.append((t.resolved_at - t.created_at).total_seconds() / 3600.0)
    avg = sum(durations) / len(durations) if durations else None
    return SupportPerformanceReport(open_count=open_count, overdue_count=overdue, resolved_last_7d=len(resolved), avg_resolution_hours=avg)


async def submit_feedback(scope: AccessScope, user: User, ticket_id: str, rating: int, comment: str | None = None) -> dict:
    authorize(scope, Permission.HELPDESK_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    ticket = await _get_ticket(tenant_id, ticket_id)
    if scope.user_id != ticket.requester_user_id:
        raise AppError(code="FORBIDDEN", message="Only requester may submit feedback", status_code=403)
    if ticket.status not in {SupportTicketStatus.RESOLVED, SupportTicketStatus.CLOSED}:
        raise AppError(code="VALIDATION_ERROR", message="Ticket not resolved", status_code=422)
    if await InstitutionSupportFeedback.find_one(
        Eq(InstitutionSupportFeedback.tenant_id, tenant_id),
        Eq(InstitutionSupportFeedback.ticket_id, ticket_id),
    ):
        raise AppError(code="CONFLICT", message="Feedback already submitted", status_code=409)
    await InstitutionSupportFeedback(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        rating=rating,
        comment=comment,
        submitted_by=user.id,
    ).insert()
    return {"status": "recorded"}