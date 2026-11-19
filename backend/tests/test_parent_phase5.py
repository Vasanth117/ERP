"""Parent phase 5 — meetings, services, reports, security."""

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
from app.modules.academics.models import AcademicYearContext
from app.modules.auth.models import User
from app.modules.parents.college_review_service import review_link_request
from app.modules.parents.enums import ParentMeetingMode, ParentRelationshipType, ParentReportCategory
from app.modules.parents.linking_service import resolve_student_reference, submit_link_request
from app.modules.parents.meeting_portal_service import (
    create_meeting_request,
    get_meeting_availability,
    list_meeting_categories,
)
from app.modules.parents.phase5_schemas import ParentMeetingRequestCreate
from app.modules.parents.reports_portal_service import build_report, reports_dashboard
from app.modules.parents.schemas import ParentLinkRequestCreate, ParentLinkReviewDecision, StudentReferenceResolve
from app.modules.parents.security_portal_service import get_security_account
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


async def _link_parent_student(suffix: str) -> tuple[User, User, AccessScope, User]:
    tenant = Tenant(name=f"College {suffix}", code=f"p5_{suffix}")
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
        student_id="STU-500",
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
    return parent, student, parent_scope, admin


@pytest.mark.asyncio
async def test_parent_meeting_request_flow(db_ready):
    suffix = uuid4().hex[:6]
    parent, student, scope, admin = await _link_parent_student(suffix)
    cats = await list_meeting_categories(scope, parent)
    assert cats
    on_date = date.today() + timedelta(days=3)
    while on_date.weekday() >= 5:
        on_date += timedelta(days=1)
    slots = await get_meeting_availability(scope, parent, on_date=on_date)
    assert slots
    start = slots[0].slot_start
    end = slots[0].slot_end
    created = await create_meeting_request(
        scope,
        parent,
        str(student.id),
        ParentMeetingRequestCreate(
            category_code="academic_progress",
            purpose="Discuss academic progress and upcoming semester planning.",
            preferred_date=on_date,
            preferred_start=start,
            preferred_end=end,
            meeting_mode=ParentMeetingMode.ONLINE,
        ),
    )
    assert created.status == "pending_staff"


@pytest.mark.asyncio
async def test_parent_reports_and_security(db_ready):
    suffix = uuid4().hex[:6]
    parent, student, scope, _ = await _link_parent_student(suffix)
    dash = await reports_dashboard(scope, parent)
    assert dash.linked_students == 1
    export = await build_report(
        scope,
        parent,
        student_user_id=str(student.id),
        category=ParentReportCategory.CONSOLIDATED,
    )
    assert export.export_token
    account = await get_security_account(scope, parent)
    assert account.email == parent.email


@pytest.mark.asyncio
async def test_meeting_without_relationship_forbidden(db_ready):
    suffix = uuid4().hex[:6]
    parent, student, scope, _ = await _link_parent_student(suffix)
    other = User(
        email=f"other5+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Other",
        role=Role.STUDENT,
        tenant_id=parent.tenant_id,
    )
    await other.insert()
    on_date = date.today() + timedelta(days=4)
    start = datetime.now(timezone.utc) + timedelta(days=4)
    end = start + timedelta(minutes=30)
    with pytest.raises(AppError) as err:
        await create_meeting_request(
            scope,
            parent,
            str(other.id),
            ParentMeetingRequestCreate(
                category_code="other",
                purpose="Need to discuss unrelated student information.",
                preferred_date=on_date,
                preferred_start=start,
                preferred_end=end,
                meeting_mode=ParentMeetingMode.IN_PERSON,
            ),
        )
    assert err.value.status_code == 403