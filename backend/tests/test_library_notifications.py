"""Library notifications and communication tests."""

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.library.library_enums import LibraryCirculationStatus
from app.modules.library.library_models import LibraryCirculation
from app.modules.library.member_schemas import MemberRegisterRequest
from app.modules.library.member_service import register_member
from app.modules.library.member_enums import LibraryMemberCategory
from app.modules.library.notification_enums import LibraryNotificationEvent
from app.modules.library.notification_models import LibraryNotification, LibraryNotificationDelivery
from app.modules.library.notification_schemas import LibraryAnnouncementCreate, ManualNotificationRequest
from app.modules.library.notification_service import (
    create_library_announcement,
    emit_library_notification,
    publish_library_announcement,
    run_notification_batch,
    send_manual_notification,
    update_preferences,
)
from app.modules.library.notification_schemas import LibraryNotificationPreferenceUpdate
from app.modules.library.notification_triggers import on_loan_issued
from app.modules.messaging.outbox_models import DomainOutboxEvent
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


def _scope(user: User, role: Role) -> AccessScope:
    return AccessScope(
        role=role,
        user_id=user.id,
        tenant_id=user.tenant_id,
        department_id=None,
        effective_permissions=permissions_for_role(role),
    )


async def _seed(suffix: str) -> tuple[AccessScope, AccessScope, AccessScope, User, User]:
    tenant = Tenant(name=f"Ntf {suffix}", code=f"ntf_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+ntf+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    lib = User(
        email=f"lib+ntf+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Lib",
        role=Role.LIBRARIAN,
        tenant_id=tenant.id,
    )
    student = User(
        email=f"stu+ntf+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Stu",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await admin.insert()
    await lib.insert()
    await student.insert()
    await register_member(
        _scope(lib, Role.LIBRARIAN),
        MemberRegisterRequest(member_user_id=str(student.id), member_category=LibraryMemberCategory.STUDENT),
    )
    return _scope(lib, Role.LIBRARIAN), _scope(admin, Role.COLLEGE_ADMIN), _scope(student, Role.STUDENT), lib, student


@pytest.mark.anyio
async def test_issue_notification_dedupe_and_template(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, _, _, _, student = await _seed(suffix)
    circ = LibraryCirculation(
        tenant_id=student.tenant_id,
        circulation_id=f"circ_{suffix}",
        student_user_id=student.id,
        copy_id=f"cp_{suffix}",
        book_id=f"b_{suffix}",
        title="Physics Vol 1",
        branch_code="MAIN",
        status=LibraryCirculationStatus.ACTIVE,
        issued_at=datetime.now(timezone.utc),
        due_at=date.today() + timedelta(days=7),
    )
    await circ.insert()
    await on_loan_issued(student.tenant_id, circ)
    await on_loan_issued(student.tenant_id, circ)
    count = await LibraryNotification.find({"tenant_id": student.tenant_id, "event_type": LibraryNotificationEvent.ISSUE.value}).count()
    assert count == 1
    deliveries = await LibraryNotificationDelivery.find({"tenant_id": student.tenant_id}).to_list()
    assert any(d.status == "sent" for d in deliveries)
    outbox = await DomainOutboxEvent.find({"tenant_id": student.tenant_id, "event_type": "library.notification.dispatch"}).count()
    assert outbox >= 1


@pytest.mark.anyio
async def test_preferences_block_and_tenant_isolation(db_ready) -> None:
    suffix = uuid4().hex[:8]
    lib_scope, _, _, _, student = await _seed(suffix)
    other_tenant = Tenant(name="Other", code=f"oth_{suffix}")
    await other_tenant.insert()
    other_student = User(
        email=f"oth+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="O",
        role=Role.STUDENT,
        tenant_id=other_tenant.id,
    )
    await other_student.insert()
    await update_preferences(lib_scope, str(student.id), LibraryNotificationPreferenceUpdate(fine_enabled=False))
    doc = await emit_library_notification(
        student.tenant_id,
        event_type=LibraryNotificationEvent.FINE,
        recipient_user_id=student.id,
        dedupe_key=f"fine:{suffix}",
        template_kwargs={"amount": "50", "reason": "Late"},
    )
    assert doc is None
    with pytest.raises(AppError) as bad:
        await send_manual_notification(
            lib_scope,
            ManualNotificationRequest(recipient_user_id=str(other_student.id), title="Hi", body="Nope"),
        )
    assert bad.value.status_code == 422


@pytest.mark.anyio
async def test_announcement_batch_and_manual(db_ready) -> None:
    suffix = uuid4().hex[:8]
    lib_scope, admin_scope, _, _, student = await _seed(suffix)
    ann = await create_library_announcement(lib_scope, LibraryAnnouncementCreate(title="Holiday hours", body="Closed Sunday"))
    pub = await publish_library_announcement(admin_scope, ann.announcement_id)
    assert pub["notifications_sent"] >= 1
    sent = await send_manual_notification(
        lib_scope,
        ManualNotificationRequest(recipient_user_id=str(student.id), title="Desk notice", body="ID required"),
    )
    assert sent.notification_id
    circ = LibraryCirculation(
        tenant_id=student.tenant_id,
        circulation_id=f"circ2_{suffix}",
        student_user_id=student.id,
        copy_id=f"cp2_{suffix}",
        book_id=f"b2_{suffix}",
        title="Chem",
        issued_at=datetime.now(timezone.utc),
        due_at=date.today() + timedelta(days=1),
        status=LibraryCirculationStatus.ACTIVE,
    )
    await circ.insert()
    stats = await run_notification_batch(lib_scope)
    assert stats["due_upcoming"] >= 0