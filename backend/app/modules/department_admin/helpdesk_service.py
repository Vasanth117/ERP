"""Department Admin — departmental helpdesk tickets."""

from __future__ import annotations

from collections import Counter

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, GTE, LTE

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.department_admin.audit_helpers import record_department_audit
from app.modules.auth.models import User
from app.modules.department_admin.department_scope import assert_faculty_visible_to_department
from app.modules.department_admin.helpdesk_constants import HELPDESK_CATEGORIES, STATUS_TRANSITIONS
from app.modules.department_admin.models import (
    DepartmentDocument,
    DepartmentHelpdeskComment,
    DepartmentHelpdeskEscalationTarget,
    DepartmentHelpdeskHistory,
    DepartmentHelpdeskStatus,
    DepartmentHelpdeskTicket,
)
from app.modules.department_admin.phase10_schemas import (
    HelpdeskAssignBody,
    HelpdeskCommentBody,
    HelpdeskCommentRead,
    HelpdeskEscalateBody,
    HelpdeskFilters,
    HelpdeskHistoryRead,
    HelpdeskReopenBody,
    HelpdeskResolveBody,
    HelpdeskSummaryRead,
    HelpdeskTicketCreate,
    HelpdeskTicketRead,
    HelpdeskTicketUpdate,
)
from app.modules.department_admin.policy import resolve_authorized_department
from app.modules.messaging.outbox_models import DomainOutboxEvent, OutboxEventStatus

HELPDESK_ADVISORY = (
    "No institution-wide helpdesk module exists; tickets are department-scoped coordination records. "
    "Escalation targets are routed via outbox for downstream College Admin / support integration."
)

OPEN_STATUSES = frozenset(
    {
        DepartmentHelpdeskStatus.OPEN,
        DepartmentHelpdeskStatus.ASSIGNED,
        DepartmentHelpdeskStatus.IN_PROGRESS,
        DepartmentHelpdeskStatus.WAITING_FOR_INFORMATION,
        DepartmentHelpdeskStatus.ESCALATED,
        DepartmentHelpdeskStatus.REOPENED,
    }
)


def _audit_meta(central_id: PydanticObjectId) -> dict:
    return {"central_department_id": str(central_id)}


def _is_overdue(ticket: DepartmentHelpdeskTicket) -> bool:
    now = utcnow()
    if ticket.status in {DepartmentHelpdeskStatus.RESOLVED, DepartmentHelpdeskStatus.CLOSED}:
        return False
    if ticket.resolution_due_at and ticket.resolution_due_at < now:
        return True
    if ticket.first_response_due_at and ticket.first_response_due_at < now and ticket.status == DepartmentHelpdeskStatus.OPEN:
        return True
    if ticket.preferred_resolution_at and ticket.preferred_resolution_at < now:
        return True
    return False


def _ticket_read(ticket: DepartmentHelpdeskTicket) -> HelpdeskTicketRead:
    return HelpdeskTicketRead(
        ticket_id=str(ticket.id),
        ticket_number=ticket.ticket_number,
        title=ticket.title,
        description=ticket.description,
        category=ticket.category,
        priority=ticket.priority,
        affected_module=ticket.affected_module,
        affected_record_type=ticket.affected_record_type,
        affected_record_id=ticket.affected_record_id,
        requester_user_id=str(ticket.requester_user_id),
        assigned_user_id=str(ticket.assigned_user_id) if ticket.assigned_user_id else None,
        assigned_team=ticket.assigned_team,
        status=ticket.status,
        escalation_target=ticket.escalation_target,
        document_ids=[str(d) for d in ticket.document_ids],
        preferred_resolution_at=ticket.preferred_resolution_at,
        first_response_due_at=ticket.first_response_due_at,
        resolution_due_at=ticket.resolution_due_at,
        is_overdue=_is_overdue(ticket),
        resolved_at=ticket.resolved_at,
        resolved_by=str(ticket.resolved_by) if ticket.resolved_by else None,
        resolution_note=ticket.resolution_note,
        created_by=str(ticket.created_by),
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )


async def _history(
    *,
    tenant_id: PydanticObjectId,
    central_id: PydanticObjectId,
    ticket_id: PydanticObjectId,
    change_type: str,
    actor: User | None,
    summary: str | None,
    before: dict | None = None,
    after: dict | None = None,
) -> None:
    await DepartmentHelpdeskHistory(
        tenant_id=tenant_id,
        central_department_id=central_id,
        ticket_id=ticket_id,
        change_type=change_type,
        actor_user_id=actor.id if actor else None,
        summary=summary,
        before=before or {},
        after=after or {},
    ).insert()


async def _notify(tenant_id: PydanticObjectId, key: str, event_type: str, payload: dict) -> None:
    if await DomainOutboxEvent.find_one(Eq(DomainOutboxEvent.tenant_id, tenant_id), Eq(DomainOutboxEvent.idempotency_key, key)):
        return
    await DomainOutboxEvent(
        tenant_id=tenant_id,
        event_type=event_type,
        payload=payload,
        idempotency_key=key,
        status=OutboxEventStatus.PENDING,
    ).insert()


def _validate_category(category: str) -> None:
    if category not in HELPDESK_CATEGORIES:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Invalid helpdesk category",
            status_code=422,
            details=[{"field": "category", "allowed": sorted(HELPDESK_CATEGORIES)}],
        )


def _validate_transition(current: DepartmentHelpdeskStatus, new: DepartmentHelpdeskStatus) -> None:
    allowed = STATUS_TRANSITIONS.get(current, frozenset())
    if new not in allowed and current != new:
        raise AppError(
            code="VALIDATION_ERROR",
            message=f"Cannot transition from {current.value} to {new.value}",
            status_code=422,
        )


async def _load_ticket(tenant_id: PydanticObjectId, central_id: PydanticObjectId, ticket_id: str) -> DepartmentHelpdeskTicket:
    ticket = await DepartmentHelpdeskTicket.get(to_object_id(ticket_id, "ticket_id"))
    if ticket is None or ticket.tenant_id != tenant_id or ticket.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Ticket not found", status_code=404)
    return ticket


async def _validate_documents(tenant_id: PydanticObjectId, central_id: PydanticObjectId, doc_ids: list[str]) -> list[PydanticObjectId]:
    out: list[PydanticObjectId] = []
    for raw in doc_ids:
        oid = to_object_id(raw, "document_id")
        doc = await DepartmentDocument.get(oid)
        if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
            raise AppError(code="FORBIDDEN", message="Document not in department", status_code=403)
        out.append(oid)
    return out


async def _next_ticket_number(tenant_id: PydanticObjectId, central_id: PydanticObjectId) -> str:
    count = await DepartmentHelpdeskTicket.find(
        Eq(DepartmentHelpdeskTicket.tenant_id, tenant_id),
        Eq(DepartmentHelpdeskTicket.central_department_id, central_id),
    ).count()
    return f"DH-{central_id}-{count + 1:05d}"


async def list_tickets(
    scope: AccessScope,
    user: User,
    pagination: Pagination,
    filters: HelpdeskFilters,
) -> Page[HelpdeskTicketRead]:
    authorize(scope, Permission.DEPARTMENT_HELPDESK_READ)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None

    query = DepartmentHelpdeskTicket.find(
        Eq(DepartmentHelpdeskTicket.tenant_id, tenant_id),
        Eq(DepartmentHelpdeskTicket.central_department_id, central_id),
    )
    if filters.category:
        query = query.find(Eq(DepartmentHelpdeskTicket.category, filters.category))
    if filters.priority:
        query = query.find(Eq(DepartmentHelpdeskTicket.priority, filters.priority))
    if filters.status:
        query = query.find(Eq(DepartmentHelpdeskTicket.status, filters.status))
    if filters.assigned_user_id:
        query = query.find(
            Eq(DepartmentHelpdeskTicket.assigned_user_id, to_object_id(filters.assigned_user_id, "assigned_user_id"))
        )
    if filters.requester_user_id:
        query = query.find(
            Eq(DepartmentHelpdeskTicket.requester_user_id, to_object_id(filters.requester_user_id, "requester_user_id"))
        )
    if filters.date_from:
        query = query.find(GTE(DepartmentHelpdeskTicket.created_at, filters.date_from))
    if filters.date_to:
        query = query.find(LTE(DepartmentHelpdeskTicket.created_at, filters.date_to))
    if filters.escalated_only:
        query = query.find(Eq(DepartmentHelpdeskTicket.status, DepartmentHelpdeskStatus.ESCALATED))

    rows = await query.sort("-created_at").to_list()
    if filters.q:
        needle = filters.q.lower()
        rows = [r for r in rows if needle in r.title.lower() or needle in r.description.lower()]
    if filters.overdue_only:
        rows = [r for r in rows if _is_overdue(r)]

    total = len(rows)
    page_rows = rows[pagination.offset : pagination.offset + pagination.limit]
    return Page(
        items=[_ticket_read(r) for r in page_rows],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def helpdesk_summary(scope: AccessScope, user: User, filters: HelpdeskFilters) -> HelpdeskSummaryRead:
    authorize(scope, Permission.DEPARTMENT_HELPDESK_READ)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None

    page = await list_tickets(scope, user, Pagination(offset=0, limit=5000), filters)
    items = page.items
    status_counts = Counter(i.status for i in items)
    overdue = sum(1 for i in items if i.is_overdue)
    categories = Counter(i.category for i in items)
    return HelpdeskSummaryRead(
        total=len(items),
        open=status_counts.get(DepartmentHelpdeskStatus.OPEN, 0),
        assigned=status_counts.get(DepartmentHelpdeskStatus.ASSIGNED, 0),
        in_progress=status_counts.get(DepartmentHelpdeskStatus.IN_PROGRESS, 0),
        waiting_for_information=status_counts.get(DepartmentHelpdeskStatus.WAITING_FOR_INFORMATION, 0),
        escalated=status_counts.get(DepartmentHelpdeskStatus.ESCALATED, 0),
        resolved=status_counts.get(DepartmentHelpdeskStatus.RESOLVED, 0),
        closed=status_counts.get(DepartmentHelpdeskStatus.CLOSED, 0),
        overdue=overdue,
        by_category=dict(categories),
        advisory=HELPDESK_ADVISORY,
        generated_at=utcnow(),
    )


async def create_ticket(scope: AccessScope, user: User, payload: HelpdeskTicketCreate) -> HelpdeskTicketRead:
    authorize(scope, Permission.DEPARTMENT_HELPDESK_MANAGE)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None

    if payload.idempotency_key:
        existing = await DepartmentHelpdeskTicket.find_one(
            Eq(DepartmentHelpdeskTicket.tenant_id, tenant_id),
            Eq(DepartmentHelpdeskTicket.idempotency_key, payload.idempotency_key),
        )
        if existing:
            return _ticket_read(existing)

    _validate_category(payload.category)
    requester = to_object_id(payload.requester_user_id, "requester_user_id") if payload.requester_user_id else user.id
    doc_ids = await _validate_documents(tenant_id, central_id, payload.document_ids)

    ticket = DepartmentHelpdeskTicket(
        tenant_id=tenant_id,
        central_department_id=central_id,
        ticket_number=await _next_ticket_number(tenant_id, central_id),
        title=payload.title.strip(),
        description=payload.description,
        category=payload.category,
        priority=payload.priority,
        affected_module=payload.affected_module,
        affected_record_type=payload.affected_record_type,
        affected_record_id=payload.affected_record_id,
        requester_user_id=requester,
        document_ids=doc_ids,
        preferred_resolution_at=payload.preferred_resolution_at,
        status=DepartmentHelpdeskStatus.OPEN,
        created_by=user.id,
        idempotency_key=payload.idempotency_key,
    )
    await ticket.insert()
    await _history(
        tenant_id=tenant_id,
        central_id=central_id,
        ticket_id=ticket.id,
        change_type="created",
        actor=user,
        summary="Ticket created",
    )
    await record_department_audit(
        actor_id=user.id,
        action="department.helpdesk.created",
        resource_type="department_helpdesk_ticket",
        resource_id=str(ticket.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
        metadata=_audit_meta(central_id),
    )
    return _ticket_read(ticket)


async def get_ticket(scope: AccessScope, user: User, ticket_id: str) -> HelpdeskTicketRead:
    authorize(scope, Permission.DEPARTMENT_HELPDESK_READ)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    return _ticket_read(await _load_ticket(tenant_id, central_id, ticket_id))


async def update_ticket(
    scope: AccessScope,
    user: User,
    ticket_id: str,
    payload: HelpdeskTicketUpdate,
) -> HelpdeskTicketRead:
    authorize(scope, Permission.DEPARTMENT_HELPDESK_MANAGE)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    ticket = await _load_ticket(tenant_id, central_id, ticket_id)
    if ticket.status == DepartmentHelpdeskStatus.CLOSED:
        raise AppError(code="FORBIDDEN", message="Closed tickets cannot be edited", status_code=403)

    before = {"status": ticket.status.value, "priority": ticket.priority.value}
    if payload.title is not None:
        ticket.title = payload.title.strip()
    if payload.description is not None:
        ticket.description = payload.description
    if payload.category is not None:
        _validate_category(payload.category)
        ticket.category = payload.category
    if payload.priority is not None:
        ticket.priority = payload.priority
    if payload.affected_module is not None:
        ticket.affected_module = payload.affected_module
    if payload.affected_record_type is not None:
        ticket.affected_record_type = payload.affected_record_type
    if payload.affected_record_id is not None:
        ticket.affected_record_id = payload.affected_record_id
    if payload.status is not None:
        _validate_transition(ticket.status, payload.status)
        ticket.status = payload.status

    ticket.updated_at = utcnow()
    await ticket.save()
    after = {"status": ticket.status.value, "priority": ticket.priority.value}
    await _history(
        tenant_id=tenant_id,
        central_id=central_id,
        ticket_id=ticket.id,
        change_type="updated",
        actor=user,
        summary="Ticket updated",
        before=before,
        after=after,
    )
    await record_department_audit(
        actor_id=user.id,
        action="department.helpdesk.updated",
        resource_type="department_helpdesk_ticket",
        resource_id=str(ticket.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
        metadata=_audit_meta(central_id),
    )
    return _ticket_read(ticket)


async def assign_ticket(scope: AccessScope, user: User, ticket_id: str, body: HelpdeskAssignBody) -> HelpdeskTicketRead:
    authorize(scope, Permission.DEPARTMENT_HELPDESK_MANAGE)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    ticket = await _load_ticket(tenant_id, central_id, ticket_id)

    assignee: PydanticObjectId | None = None
    if body.assigned_user_id:
        assignee = to_object_id(body.assigned_user_id, "assigned_user_id")
        await assert_faculty_visible_to_department(tenant_id, central_id, assignee)

    before = {
        "assigned_user_id": str(ticket.assigned_user_id) if ticket.assigned_user_id else None,
        "status": ticket.status.value,
    }
    ticket.assigned_user_id = assignee
    ticket.assigned_team = body.assigned_team
    if ticket.status in {DepartmentHelpdeskStatus.OPEN, DepartmentHelpdeskStatus.REOPENED}:
        ticket.status = DepartmentHelpdeskStatus.ASSIGNED
    ticket.updated_at = utcnow()
    await ticket.save()
    await _history(
        tenant_id=tenant_id,
        central_id=central_id,
        ticket_id=ticket.id,
        change_type="assign",
        actor=user,
        summary=body.reason or "Assigned",
        before=before,
        after={"assigned_user_id": str(assignee) if assignee else None, "status": ticket.status.value},
    )
    await record_department_audit(
        actor_id=user.id,
        action="department.helpdesk.assigned",
        resource_type="department_helpdesk_ticket",
        resource_id=str(ticket.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
        metadata=_audit_meta(central_id),
    )
    return _ticket_read(ticket)


async def add_comment(
    scope: AccessScope,
    user: User,
    ticket_id: str,
    body: HelpdeskCommentBody,
) -> HelpdeskCommentRead:
    authorize(scope, Permission.DEPARTMENT_HELPDESK_MANAGE)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    ticket = await _load_ticket(tenant_id, central_id, ticket_id)
    attachments = await _validate_documents(tenant_id, central_id, body.attachment_document_ids)

    if body.is_internal and Permission.DEPARTMENT_HELPDESK_MANAGE not in scope.effective_permissions:
        raise AppError(code="FORBIDDEN", message="Cannot post internal notes", status_code=403)

    comment = DepartmentHelpdeskComment(
        tenant_id=tenant_id,
        central_department_id=central_id,
        ticket_id=ticket.id,
        body=body.body,
        is_internal=body.is_internal,
        author_user_id=user.id,
        attachment_document_ids=attachments,
    )
    await comment.insert()
    if ticket.status == DepartmentHelpdeskStatus.OPEN:
        ticket.first_response_due_at = ticket.first_response_due_at or utcnow()
    ticket.updated_at = utcnow()
    await ticket.save()
    await _history(
        tenant_id=tenant_id,
        central_id=central_id,
        ticket_id=ticket.id,
        change_type="comment",
        actor=user,
        summary="Internal comment" if body.is_internal else "Comment added",
    )
    return HelpdeskCommentRead(
        comment_id=str(comment.id),
        body=comment.body,
        is_internal=comment.is_internal,
        author_user_id=str(comment.author_user_id),
        attachment_document_ids=[str(d) for d in comment.attachment_document_ids],
        created_at=comment.created_at,
    )


async def list_comments(
    scope: AccessScope,
    user: User,
    ticket_id: str,
    pagination: Pagination,
    *,
    include_internal: bool = True,
) -> Page[HelpdeskCommentRead]:
    authorize(scope, Permission.DEPARTMENT_HELPDESK_READ)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    ticket = await _load_ticket(tenant_id, central_id, ticket_id)

    query = DepartmentHelpdeskComment.find(
        Eq(DepartmentHelpdeskComment.tenant_id, tenant_id),
        Eq(DepartmentHelpdeskComment.ticket_id, ticket.id),
    )
    rows = await query.sort("+created_at").to_list()
    if not include_internal or Permission.DEPARTMENT_HELPDESK_MANAGE not in scope.effective_permissions:
        rows = [r for r in rows if not r.is_internal]
    total = len(rows)
    page_rows = rows[pagination.offset : pagination.offset + pagination.limit]
    return Page(
        items=[
            HelpdeskCommentRead(
                comment_id=str(r.id),
                body=r.body,
                is_internal=r.is_internal,
                author_user_id=str(r.author_user_id),
                attachment_document_ids=[str(d) for d in r.attachment_document_ids],
                created_at=r.created_at,
            )
            for r in page_rows
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def escalate_ticket(scope: AccessScope, user: User, ticket_id: str, body: HelpdeskEscalateBody) -> HelpdeskTicketRead:
    authorize(scope, Permission.DEPARTMENT_HELPDESK_MANAGE)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    ticket = await _load_ticket(tenant_id, central_id, ticket_id)
    _validate_transition(ticket.status, DepartmentHelpdeskStatus.ESCALATED)

    before = {"status": ticket.status.value, "escalation_target": ticket.escalation_target.value if ticket.escalation_target else None}
    ticket.status = DepartmentHelpdeskStatus.ESCALATED
    ticket.escalation_target = body.escalation_target
    ticket.escalation_note = body.note
    ticket.updated_at = utcnow()
    await ticket.save()
    await _history(
        tenant_id=tenant_id,
        central_id=central_id,
        ticket_id=ticket.id,
        change_type="escalate",
        actor=user,
        summary=body.note or f"Escalated to {body.escalation_target.value}",
        before=before,
        after={"status": ticket.status.value, "escalation_target": body.escalation_target.value},
    )
    key = f"dept_helpdesk_escalate:{ticket.id}:{body.escalation_target.value}"
    await _notify(
        tenant_id,
        key,
        "department.helpdesk.escalated",
        {"ticket_id": str(ticket.id), "target": body.escalation_target.value, "note": body.note},
    )
    await record_department_audit(
        actor_id=user.id,
        action="department.helpdesk.escalated",
        resource_type="department_helpdesk_ticket",
        resource_id=str(ticket.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
        metadata={**_audit_meta(central_id), "target": body.escalation_target.value},
    )
    return _ticket_read(ticket)


async def resolve_ticket(scope: AccessScope, user: User, ticket_id: str, body: HelpdeskResolveBody) -> HelpdeskTicketRead:
    authorize(scope, Permission.DEPARTMENT_HELPDESK_MANAGE)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    ticket = await _load_ticket(tenant_id, central_id, ticket_id)
    _validate_transition(ticket.status, DepartmentHelpdeskStatus.RESOLVED)

    ticket.status = DepartmentHelpdeskStatus.RESOLVED
    ticket.resolution_note = body.resolution_note
    ticket.resolved_by = user.id
    ticket.resolved_at = utcnow()
    ticket.updated_at = utcnow()
    await ticket.save()
    await _history(tenant_id=tenant_id, central_id=central_id, ticket_id=ticket.id, change_type="resolve", actor=user, summary="Resolved")
    await record_department_audit(
        actor_id=user.id,
        action="department.helpdesk.resolved",
        resource_type="department_helpdesk_ticket",
        resource_id=str(ticket.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
        metadata=_audit_meta(central_id),
    )
    return _ticket_read(ticket)


async def reopen_ticket(scope: AccessScope, user: User, ticket_id: str, body: HelpdeskReopenBody) -> HelpdeskTicketRead:
    authorize(scope, Permission.DEPARTMENT_HELPDESK_MANAGE)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    ticket = await _load_ticket(tenant_id, central_id, ticket_id)
    if ticket.status not in {DepartmentHelpdeskStatus.RESOLVED, DepartmentHelpdeskStatus.CLOSED}:
        raise AppError(code="VALIDATION_ERROR", message="Only resolved or closed tickets can be reopened", status_code=422)

    ticket.status = DepartmentHelpdeskStatus.REOPENED
    ticket.resolved_at = None
    ticket.resolved_by = None
    ticket.closed_at = None
    ticket.updated_at = utcnow()
    await ticket.save()
    await _history(tenant_id=tenant_id, central_id=central_id, ticket_id=ticket.id, change_type="reopen", actor=user, summary=body.reason)
    await record_department_audit(
        actor_id=user.id,
        action="department.helpdesk.reopened",
        resource_type="department_helpdesk_ticket",
        resource_id=str(ticket.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
        metadata=_audit_meta(central_id),
    )
    return _ticket_read(ticket)


async def ticket_history(
    scope: AccessScope,
    user: User,
    ticket_id: str,
    pagination: Pagination,
) -> Page[HelpdeskHistoryRead]:
    authorize(scope, Permission.DEPARTMENT_HELPDESK_READ)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    ticket = await _load_ticket(tenant_id, central_id, ticket_id)
    query = DepartmentHelpdeskHistory.find(
        Eq(DepartmentHelpdeskHistory.tenant_id, tenant_id),
        Eq(DepartmentHelpdeskHistory.ticket_id, ticket.id),
    )
    total = await query.count()
    rows = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            HelpdeskHistoryRead(
                event_id=str(r.id),
                change_type=r.change_type,
                actor_user_id=str(r.actor_user_id) if r.actor_user_id else None,
                summary=r.summary,
                before=r.before,
                after=r.after,
                created_at=r.created_at,
            )
            for r in rows
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


def list_helpdesk_categories(scope: AccessScope) -> list[str]:
    authorize(scope, Permission.DEPARTMENT_HELPDESK_READ)
    return sorted(HELPDESK_CATEGORIES)