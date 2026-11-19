"""Parent phase 3 — examinations, timetable, calendar, finance, payments, enquiries."""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.time import utcnow
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.academics.curriculum_models import EnrollmentRosterEntry
from app.modules.academics.models import AcademicYearContext
from app.modules.auth.models import User
from app.modules.finance.finance_enums import FeeDemandStatus
from app.modules.finance.finance_models import StudentFeeDemand
from app.modules.parents.college_review_service import review_link_request
from app.modules.parents.enums import ParentRelationshipType
from app.modules.parents.examination_portal_service import (
    get_examination_overview,
    get_published_results_summary,
    hall_ticket_availability_parent,
)
from app.modules.parents.finance_portal_service import (
    get_finance_dashboard,
    initiate_parent_payment,
    submit_finance_enquiry,
)
from app.modules.parents.linking_service import resolve_student_reference, submit_link_request
from app.modules.parents.phase3_schemas import ParentFinanceEnquiryCreate, ParentPaymentInitiateInput
from app.modules.parents.schemas import ParentLinkRequestCreate, ParentLinkReviewDecision, StudentReferenceResolve
from app.modules.students.models import StudentProfile
from app.modules.tenants.models import Department, Tenant


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


async def _link_parent_student(suffix: str) -> tuple[User, User, AccessScope]:
    tenant = Tenant(name=f"College {suffix}", code=f"p3_{suffix}")
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
        student_id="STU-300",
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
    await EnrollmentRosterEntry(
        tenant_id=tenant.id,
        course_id="cse101",
        course_code="CSE101",
        section_code="A",
        student_user_id=student.id,
        roll_number=roll,
        display_name="Alex Student",
        academic_year_label="2025-26",
        semester_label="Odd",
    ).insert()
    await StudentFeeDemand(
        tenant_id=tenant.id,
        student_user_id=student.id,
        demand_id=f"dem_{suffix}",
        academic_year_label="2025-26",
        semester_label="Odd",
        description="Tuition fee",
        amount=25000.0,
        due_date=date.today() + timedelta(days=14),
        status=FeeDemandStatus.OPEN,
    ).insert()
    parent_scope = AccessScope(
        role=Role.PARENT,
        user_id=parent.id,
        tenant_id=tenant.id,
        effective_permissions=permissions_for_role(Role.PARENT),
    )
    admin_scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
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
async def test_parent_examination_overview(db_ready):
    suffix = uuid4().hex[:6]
    parent, student, scope = await _link_parent_student(suffix)
    overview = await get_examination_overview(scope, parent, str(student.id))
    assert overview.academic_year_label == "2025-26"
    assert overview.semester_label == "Odd"


@pytest.mark.asyncio
async def test_parent_unpublished_results_not_exposed(db_ready):
    suffix = uuid4().hex[:6]
    parent, student, scope = await _link_parent_student(suffix)
    with pytest.raises(AppError) as err:
        await get_published_results_summary(scope, parent, str(student.id), "nonexistent-season")
    assert err.value.status_code == 404


@pytest.mark.asyncio
async def test_parent_hall_ticket_requires_permission(db_ready):
    suffix = uuid4().hex[:6]
    parent, student, scope = await _link_parent_student(suffix)
    with pytest.raises(AppError) as err:
        await hall_ticket_availability_parent(scope, parent, str(student.id), "season-1")
    assert err.value.status_code == 403


@pytest.mark.asyncio
async def test_parent_finance_dashboard_and_payment_idempotency(db_ready):
    suffix = uuid4().hex[:6]
    parent, student, scope = await _link_parent_student(suffix)
    dash = await get_finance_dashboard(scope, parent, str(student.id))
    assert dash.outstanding_amount >= 0
    idem = f"idem_{suffix}"
    payload = ParentPaymentInitiateInput(
        demand_id=f"dem_{suffix}",
        idempotency_key=idem,
        payment_mode="offline",
        offline_reference="CHQ-001",
    )
    first = await initiate_parent_payment(scope, parent, str(student.id), payload)
    second = await initiate_parent_payment(scope, parent, str(student.id), payload)
    assert first.transaction_id == second.transaction_id
    assert first.amount == second.amount


@pytest.mark.asyncio
async def test_parent_finance_enquiry(db_ready):
    suffix = uuid4().hex[:6]
    parent, student, scope = await _link_parent_student(suffix)
    enquiry = await submit_finance_enquiry(
        scope,
        parent,
        str(student.id),
        ParentFinanceEnquiryCreate(
            category="payment_discrepancy",
            description="Payment shows success but balance unchanged.",
        ),
    )
    assert enquiry.status == "submitted"