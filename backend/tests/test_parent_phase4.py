"""Parent phase 4 — communication, documents, service requests, support."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.schemas import Pagination
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.academics.models import AcademicCalendarEvent, AcademicYearContext
from app.modules.auth.models import User
from app.modules.parents.college_review_service import review_link_request
from app.modules.parents.communication_portal_service import (
    get_communication_dashboard,
    list_notifications,
    mark_notification_read,
)
from app.modules.parents.enums import ParentRelationshipType, ParentServiceRequestCategory
from app.modules.parents.linking_service import resolve_student_reference, submit_link_request
from app.modules.parents.phase4_schemas import ParentServiceRequestCreate, ParentSupportEnquiryCreate
from app.modules.parents.schemas import ParentLinkRequestCreate, ParentLinkReviewDecision, StudentReferenceResolve
from app.modules.parents.service_request_service import create_service_request, list_service_requests
from app.modules.parents.support_portal_service import submit_support_enquiry
from app.modules.students.models import StudentProfile
from app.modules.tenants.models import Department, Tenant


from db_helpers import drop_all_test_collections


@pytest.fixture
async def db_ready():
    try:
        await drop_all_test_collections()
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


async def _link_parent_student(suffix: str) -> tuple[User, User, AccessScope]:
    tenant = Tenant(name=f"College {suffix}", code=f"p4_{suffix}")
    await tenant.insert()
    department = Department(tenant_id=tenant.id, name="CSE", code="CSE")
    await department.insert()
    student = User(
        email=f"student+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Alex Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
        department_id=department.id,
    )
    await student.insert()
    parent = User(
        email=f"parent+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Pat Parent",
        role=Role.PARENT,
        tenant_id=tenant.id,
    )
    await parent.insert()
    admin = User(
        email=f"admin+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    roll = f"21CSE{suffix[:3]}"
    await StudentProfile(
        tenant_id=tenant.id,
        user_id=student.id,
        student_id="STU-400",
        roll_number=roll,
        programme_code="BTECH-CSE",
        programme_name="B.Tech CSE",
        batch_label="2021",
        section_code="A",
    ).insert()
    await AcademicYearContext(
        tenant_id=tenant.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        is_current=True,
    ).insert()
    await AcademicCalendarEvent(
        tenant_id=tenant.id,
        title="Parent Orientation",
        description="Welcome parents",
        event_at=datetime.now(timezone.utc),
        event_type="event",
        audience="parents",
    ).insert()
    parent_scope = AccessScope(
        role=Role.PARENT,
        user_id=parent.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.PARENT),
    )
    admin_scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    preview = await resolve_student_reference(
        parent_scope,
        parent,
        StudentReferenceResolve(reference_type="roll_number", reference_value=roll),
    )
    req = await submit_link_request(
        parent_scope,
        parent,
        ParentLinkRequestCreate(
            hint_token=preview.hint_token,
            relationship_type=ParentRelationshipType.MOTHER,
            relationship_declaration="I am the mother of this student for institutional verification.",
        ),
    )
    await review_link_request(
        admin_scope,
        __import__("beanie").PydanticObjectId(req.request_id),
        ParentLinkReviewDecision(decision="approve"),
        reviewer_id=admin.id,
    )
    return parent, student, parent_scope


@pytest.mark.asyncio
async def test_parent_communication_dashboard_and_read(db_ready):
    suffix = uuid4().hex[:6]
    parent, student, scope = await _link_parent_student(suffix)
    dash = await get_communication_dashboard(scope, parent)
    assert dash.total_notifications >= 1
    page = await list_notifications(scope, parent, Pagination(limit=50, offset=0))
    assert page.total >= 1
    key = page.items[0].notification_key
    await mark_notification_read(scope, parent, key)
    page2 = await list_notifications(scope, parent, Pagination(limit=50, offset=0), unread_only=True)
    assert all(i.notification_key != key for i in page2.items)


@pytest.mark.asyncio
async def test_parent_service_request_and_support(db_ready):
    suffix = uuid4().hex[:6]
    parent, student, scope = await _link_parent_student(suffix)
    created = await create_service_request(
        scope,
        parent,
        str(student.id),
        ParentServiceRequestCreate(
            category=ParentServiceRequestCategory.ACADEMIC,
            request_type="academic_information",
            subject="Programme structure",
            description="Please share the current semester course structure for verification.",
        ),
    )
    assert created.status == "submitted"
    rows = await list_service_requests(scope, parent, str(student.id))
    assert any(r.request_id == created.request_id for r in rows)
    support = await submit_support_enquiry(
        scope,
        parent,
        ParentSupportEnquiryCreate(
            category="parent_account",
            subject="Login issue",
            description="I need help signing in to the parent portal after password reset.",
        ),
    )
    assert support.helpdesk_ticket_id


@pytest.mark.asyncio
async def test_unlinked_student_communication_filter(db_ready):
    suffix = uuid4().hex[:6]
    parent, student, scope = await _link_parent_student(suffix)
    other = User(
        email=f"other4+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Other",
        role=Role.STUDENT,
        tenant_id=parent.tenant_id,
    )
    await other.insert()
    with pytest.raises(AppError) as err:
        await list_notifications(
            scope, parent, Pagination(limit=10, offset=0), student_user_id=str(other.id)
        )
    assert err.value.status_code == 403