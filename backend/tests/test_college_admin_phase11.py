"""College Admin phase 11 — helpdesk and support."""

from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission, permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.helpdesk_admin_models import SupportTicketStatus
from app.modules.college_admin.helpdesk_admin_schemas import (
    SupportAssignRequest,
    SupportCommentCreate,
    SupportInternalNoteCreate,
    SupportReopenRequest,
    SupportResolveRequest,
    SupportTicketCreate,
    SupportTicketUpdate,
)
from app.modules.college_admin.helpdesk_admin_service import (
    add_comment,
    add_internal_note,
    assign_ticket,
    create_ticket,
    get_ticket_detail,
    reopen_ticket,
    resolve_ticket,
    support_performance_report,
    update_ticket,
)
from app.modules.tenants.models import Tenant


@pytest.fixture
async def db_ready():
    try:
        await connect_to_mongo()
    except Exception as exc:
        pytest.skip(f"MongoDB not available: {exc}")
    try:
        await connect_redis()
    except Exception:
        pass
    for model in document_models():
        await model.get_motor_collection().delete_many({})
    yield
    await close_redis()
    await close_mongo()


async def _seed_admin(suffix: str) -> tuple[Tenant, User, AccessScope]:
    tenant = Tenant(name=f"College P11 {suffix}", code=f"p11_{suffix}")
    await tenant.insert()
    user = User(
        email=f"admin+p11+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="College Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await user.insert()
    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=user.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    return tenant, user, scope


@pytest.mark.anyio
async def test_ticket_lifecycle(db_ready):
    tenant, admin, scope = await _seed_admin(uuid4().hex[:6])
    staff = User(
        email=f"staff+{uuid4().hex[:6]}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Staff",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await staff.insert()
    ticket = await create_ticket(
        scope,
        admin,
        SupportTicketCreate(
            title="Network issue",
            description="Cannot access LMS",
            category_code="it",
            module_key="platform",
            issue_type="access",
            idempotency_key=f"idem_{uuid4().hex[:8]}",
        ),
    )
    assert ticket.status == SupportTicketStatus.OPEN
    assigned = await assign_ticket(scope, admin, ticket.ticket_id, SupportAssignRequest(assignee_user_id=str(staff.id), assigned_team="it"))
    assert assigned.assigned_user_id == str(staff.id)
    await add_comment(scope, admin, ticket.ticket_id, SupportCommentCreate(body="Checking logs"))
    await add_internal_note(scope, admin, ticket.ticket_id, SupportInternalNoteCreate(body="VPN misconfigured"))
    await update_ticket(scope, admin, ticket.ticket_id, SupportTicketUpdate(status=SupportTicketStatus.IN_PROGRESS))
    resolved = await resolve_ticket(scope, admin, ticket.ticket_id, SupportResolveRequest(resolution_detail="Reset VPN profile"))
    assert resolved.status == SupportTicketStatus.RESOLVED
    reopened = await reopen_ticket(scope, admin, ticket.ticket_id, SupportReopenRequest(reason="Issue returned"))
    assert reopened.status == SupportTicketStatus.REOPENED
    report = await support_performance_report(scope)
    assert report.open_count >= 1


@pytest.mark.anyio
async def test_internal_notes_hidden_from_requester(db_ready):
    tenant, admin, admin_scope = await _seed_admin(uuid4().hex[:6])
    requester = User(
        email=f"req+{uuid4().hex[:6]}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Requester",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await requester.insert()
    req_scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=requester.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=frozenset({Permission.HELPDESK_ADMIN_READ}),
    )
    ticket = await create_ticket(
        admin_scope,
        admin,
        SupportTicketCreate(
            title="Fee issue",
            description="Wrong demand",
            category_code="finance",
            module_key="finance",
            issue_type="billing",
            requester_user_id=str(requester.id),
        ),
    )
    await add_internal_note(admin_scope, admin, ticket.ticket_id, SupportInternalNoteCreate(body="Sensitive payroll link"))
    detail = await get_ticket_detail(req_scope, ticket.ticket_id, include_internal=False)
    assert detail.internal_notes is None
    with pytest.raises(AppError) as exc:
        await get_ticket_detail(req_scope, ticket.ticket_id, include_internal=True)
    assert exc.value.status_code == 403


@pytest.mark.anyio
async def test_tenant_isolation(db_ready):
    _, admin1, scope1 = await _seed_admin(uuid4().hex[:6])
    t2, _, scope2 = await _seed_admin(uuid4().hex[:6])
    ticket = await create_ticket(
        scope1,
        admin1,
        SupportTicketCreate(
            title="Isolated",
            description="Test",
            category_code="academic",
            module_key="academics",
            issue_type="general",
        ),
    )
    with pytest.raises(AppError) as exc:
        await get_ticket_detail(scope2, ticket.ticket_id)
    assert exc.value.status_code == 404
    assert t2.id is not None