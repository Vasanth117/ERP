"""Parent phase 2 — student profile, academics, attendance, alerts, enquiries."""

from datetime import date
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
from app.modules.academics.curriculum_models import EnrollmentRosterEntry
from app.modules.academics.models import AcademicYearContext
from app.modules.attendance.enums import AttendanceMarkStatus, AttendanceSessionStatus
from app.modules.attendance.models import AttendancePolicyReference, AttendanceRecord, AttendanceSession
from app.modules.auth.models import User
from app.modules.parents.academic_overview_service import get_academic_overview, get_student_profile_view
from app.modules.parents.attendance_monitoring_service import (
    acknowledge_alert,
    get_attendance_dashboard,
    list_attendance_alerts,
    submit_attendance_enquiry,
)
from app.modules.parents.college_review_service import review_link_request
from app.modules.parents.enums import ParentRelationshipType
from app.modules.parents.linking_service import resolve_student_reference, submit_link_request
from app.modules.parents.phase2_schemas import ParentAttendanceEnquiryCreate
from app.modules.parents.schemas import ParentLinkRequestCreate, ParentLinkReviewDecision, StudentReferenceResolve
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


async def _link_parent_student(suffix: str) -> tuple[User, User, AccessScope]:
    tenant = Tenant(name=f"College {suffix}", code=f"p2_{suffix}")
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
        student_id="STU-200",
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
    await StudentAcademicRecord(
        tenant_id=tenant.id,
        user_id=student.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        cgpa=8.2,
        credits_registered=18,
        credits_earned=16,
    ).insert()
    await AttendancePolicyReference(
        tenant_id=tenant.id,
        policy_code="default",
        is_active=True,
    ).insert()
    session = AttendanceSession(
        tenant_id=tenant.id,
        faculty_user_id=student.id,
        course_id="cse101",
        course_code="CSE101",
        section="A",
        academic_year_label="2025-26",
        semester_label="Odd",
        session_date=date.today(),
        status=AttendanceSessionStatus.LOCKED,
    )
    await session.insert()
    await AttendanceRecord(
        tenant_id=tenant.id,
        session_id=session.id,
        student_user_id=student.id,
        status=AttendanceMarkStatus.ABSENT,
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
async def test_parent_student_profile_and_academics(db_ready):
    suffix = uuid4().hex[:6]
    parent, student, scope = await _link_parent_student(suffix)
    profile = await get_student_profile_view(scope, parent, str(student.id))
    assert profile.roll_number
    overview = await get_academic_overview(scope, parent, str(student.id))
    assert overview.enrolled_courses
    assert overview.progress is not None
    assert overview.progress.cgpa == 8.2


@pytest.mark.asyncio
async def test_parent_attendance_alerts_and_enquiry(db_ready):
    suffix = uuid4().hex[:6]
    parent, student, scope = await _link_parent_student(suffix)
    dash = await get_attendance_dashboard(scope, parent, str(student.id))
    assert dash.summary.academic_year_label == "2025-26"
    alerts = await list_attendance_alerts(scope, parent, str(student.id))
    assert alerts
    ack = await acknowledge_alert(scope, parent, str(student.id), alerts[0].alert_id)
    assert ack["acknowledged_at"]
    enquiry = await submit_attendance_enquiry(
        scope,
        parent,
        str(student.id),
        ParentAttendanceEnquiryCreate(
            category="incorrect_status",
            course_code="CSE101",
            section="A",
            attendance_date=date.today(),
            description="Attendance status appears incorrect for this session.",
        ),
    )
    assert enquiry.status == "submitted"


@pytest.mark.asyncio
async def test_unlinked_student_forbidden(db_ready):
    suffix = uuid4().hex[:6]
    parent, student, scope = await _link_parent_student(suffix)
    other = User(
        email=f"other2+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Other",
        role=Role.STUDENT,
        tenant_id=parent.tenant_id,
    )
    await other.insert()
    with pytest.raises(AppError) as err:
        await get_student_profile_view(scope, parent, str(other.id))
    assert err.value.status_code == 403