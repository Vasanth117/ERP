"""Parent phase 1 — dashboard, account, and student linking."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.academics.curriculum_models import EnrollmentRosterEntry
from app.modules.academics.models import AcademicYearContext
from app.modules.auth.models import User
from app.modules.parents.dashboard_service import get_parent_dashboard
from app.modules.parents.enums import ParentRelationshipType
from app.modules.parents.linking_service import resolve_student_reference, submit_link_request
from app.modules.parents.profile_service import get_parent_profile, update_parent_profile
from app.modules.parents.schemas import (
    ParentDashboardFilters,
    ParentLinkRequestCreate,
    ParentLinkReviewDecision,
    ParentProfileUpdate,
    StudentReferenceResolve,
)
from app.modules.students.models import StudentAcademicRecord, StudentProfile
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


async def _seed_parent_student(suffix: str) -> tuple[Tenant, User, User, AccessScope, AccessScope]:
    tenant = Tenant(name=f"College {suffix}", code=f"pc_{suffix}")
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
        full_name="College Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    await StudentProfile(
        tenant_id=tenant.id,
        user_id=student.id,
        student_id="STU-100",
        roll_number=f"21CSE{suffix[:3]}",
        programme_code="BTECH-CSE",
        programme_name="B.Tech CSE",
        batch_label="2021",
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
        roll_number=f"21CSE{suffix[:3]}",
        display_name="Alex Student",
        academic_year_label="2025-26",
        semester_label="Odd",
    ).insert()
    await StudentAcademicRecord(
        tenant_id=tenant.id,
        user_id=student.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        fee_snapshot={"status": "available", "outstanding_amount": 5000, "currency": "INR"},
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
    return tenant, student, parent, parent_scope, admin_scope


@pytest.mark.asyncio
async def test_parent_profile_and_linking_flow(db_ready):
    suffix = uuid4().hex[:6]
    _, student, parent, parent_scope, admin_scope = await _seed_parent_student(suffix)

    profile = await get_parent_profile(parent_scope, parent)
    assert profile.account_status.value == "active"

    updated = await update_parent_profile(
        parent_scope, parent, ParentProfileUpdate(contact_phone="+919999999999")
    )
    assert updated.contact_phone == "+919999999999"
    assert updated.mobile_verified is False

    preview = await resolve_student_reference(
        parent_scope,
        parent,
        StudentReferenceResolve(reference_type="roll_number", reference_value=f"21CSE{suffix[:3]}"),
    )
    assert preview.masked_display_name.endswith("***")

    req = await submit_link_request(
        parent_scope,
        parent,
        ParentLinkRequestCreate(
            hint_token=preview.hint_token,
            relationship_type=ParentRelationshipType.FATHER,
            relationship_declaration="I am the father of this student per institutional records.",
        ),
    )
    assert req.status.value == "pending_verification"

    preview2 = await resolve_student_reference(
        parent_scope,
        parent,
        StudentReferenceResolve(reference_type="roll_number", reference_value=f"21CSE{suffix[:3]}"),
    )
    with pytest.raises(AppError) as dup:
        await submit_link_request(
            parent_scope,
            parent,
            ParentLinkRequestCreate(
                hint_token=preview2.hint_token,
                relationship_type=ParentRelationshipType.FATHER,
                relationship_declaration="Duplicate attempt should fail.",
            ),
        )
    assert dup.value.status_code == 409

    from app.modules.parents.college_review_service import review_link_request

    admin_user = await User.find_one({"email": f"admin+{suffix}@example.com"})
    assert admin_user is not None
    result = await review_link_request(
        admin_scope,
        __import__("beanie").PydanticObjectId(req.request_id),
        ParentLinkReviewDecision(decision="approve"),
        reviewer_id=admin_user.id,
    )
    assert result["status"] == "approved"

    dashboard = await get_parent_dashboard(parent_scope, parent, ParentDashboardFilters())
    assert dashboard.verified_linked_students == 1
    assert len(dashboard.student_summaries) == 1
    assert dashboard.student_summaries[0].student_user_id == str(student.id)


@pytest.mark.asyncio
async def test_unverified_student_dashboard_forbidden(db_ready):
    suffix = uuid4().hex[:6]
    _, student, parent, parent_scope, _ = await _seed_parent_student(suffix)
    other_parent = User(
        email=f"other+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Other Parent",
        role=Role.PARENT,
        tenant_id=parent.tenant_id,
    )
    await other_parent.insert()
    other_scope = AccessScope(
        role=Role.PARENT,
        user_id=other_parent.id,
        tenant_id=parent.tenant_id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.PARENT),
    )
    with pytest.raises(AppError) as err:
        await get_parent_dashboard(
            other_scope,
            other_parent,
            ParentDashboardFilters(student_user_id=str(student.id)),
        )
    assert err.value.status_code == 403


@pytest.mark.asyncio
async def test_cross_tenant_isolation(db_ready):
    suffix = uuid4().hex[:6]
    tenant_a, _, parent_a, scope_a, _ = await _seed_parent_student(suffix)
    tenant_b = Tenant(name="Other", code=f"oth_{suffix}")
    await tenant_b.insert()
    parent_b_scope = AccessScope(
        role=Role.PARENT,
        user_id=parent_a.id,
        tenant_id=tenant_b.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.PARENT),
    )
    with pytest.raises(AppError):
        await get_parent_profile(parent_b_scope, parent_a)