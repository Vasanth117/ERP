"""Faculty phase 3 — attendance and LMS."""

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest
from beanie import PydanticObjectId

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.academics.curriculum_models import CourseRecord, EnrollmentRosterEntry
from app.modules.attendance.enums import AttendanceMarkStatus, AttendanceSessionStatus
from app.modules.attendance.models import AttendanceSession
from app.modules.attendance.policy_engine import calculate_percentage
from app.modules.attendance.models import AttendancePolicyRules, AttendanceRecord
from app.modules.faculty.attendance_schemas import AttendanceMarkInput, AttendanceSessionCreate, AttendanceSubmitPayload
from app.modules.faculty.attendance_service import (
    attendance_shortages,
    create_attendance_session,
    submit_attendance,
)
from app.modules.faculty.enums import AssignmentRole, AssignmentStatus
from app.modules.faculty.lms_schemas import EvaluationCreate, LmsAssignmentCreate
from app.modules.faculty.lms_service import (
    create_lms_assignment,
    evaluate_submission,
    publish_lms_assignment,
)
from app.modules.faculty.models import FacultyAssignment
from app.modules.auth.models import User
from app.modules.lms import storage as lms_storage
from app.modules.lms.enums import LmsAssignmentStatus
from app.modules.lms.models import AssignmentRule, AssignmentSubmission, CourseAssignment
from app.modules.tenants.models import Department, Tenant


@pytest.fixture
async def db_ready():
    try:
        await connect_to_mongo()
        await connect_redis()
    except Exception as exc:
        pytest.skip(f"Dependencies not available: {exc}")
    for model in document_models():
        await model.get_motor_collection().delete_many({})
    yield
    await close_redis()
    await close_mongo()


async def _faculty_seed() -> tuple[AccessScope, User, PydanticObjectId, str, PydanticObjectId]:
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"C {suffix}", code=f"c3_{suffix}")
    await tenant.insert()
    dept = Department(tenant_id=tenant.id, name="CSE", code="CSE")
    await dept.insert()
    faculty = User(
        email=f"f3+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Faculty 3",
        role=Role.FACULTY,
        tenant_id=tenant.id,
        department_id=dept.id,
    )
    await faculty.insert()
    student = User(
        email=f"s+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()
    course = CourseRecord(
        tenant_id=tenant.id,
        course_id=f"cid-{suffix}",
        course_code="CS301",
        name="DBMS",
        credit_units=3,
    )
    await course.insert()
    await FacultyAssignment(
        tenant_id=tenant.id,
        user_id=faculty.id,
        course_id=course.course_id,
        course_code="CS301",
        course_name="DBMS",
        section="A",
        academic_year_label="2025-26",
        semester_label="Odd",
        assignment_role=AssignmentRole.PRIMARY,
        status=AssignmentStatus.ACTIVE,
    ).insert()
    await EnrollmentRosterEntry(
        tenant_id=tenant.id,
        course_id=course.course_id,
        course_code="CS301",
        section_code="A",
        student_user_id=student.id,
        roll_number="23CS001",
        display_name="Student",
        academic_year_label="2025-26",
        semester_label="Odd",
    ).insert()
    scope = AccessScope(
        role=Role.FACULTY,
        user_id=faculty.id,
        tenant_id=tenant.id,
        department_id=dept.id,
        effective_permissions=permissions_for_role(Role.FACULTY),
    )
    return scope, faculty, tenant.id, course.course_id, student.id


@pytest.mark.anyio
async def test_attendance_create_and_submit(db_ready) -> None:
    scope, user, _, _, student_id = await _faculty_seed()
    session = await create_attendance_session(
        scope,
        user,
        AttendanceSessionCreate(course_code="CS301", section="A", session_date=date.today()),
    )
    submitted = await submit_attendance(
        scope,
        user,
        PydanticObjectId(session.id),
        AttendanceSubmitPayload(
            marks=[AttendanceMarkInput(student_user_id=str(student_id), status=AttendanceMarkStatus.PRESENT)]
        ),
    )
    assert submitted.status.value == "submitted"


@pytest.mark.anyio
async def test_duplicate_attendance_submit_blocked(db_ready) -> None:
    scope, user, _, _, student_id = await _faculty_seed()
    created = await create_attendance_session(
        scope,
        user,
        AttendanceSessionCreate(course_code="CS301", section="A", session_date=date.today()),
    )
    await submit_attendance(
        scope,
        user,
        PydanticObjectId(created.id),
        AttendanceSubmitPayload(
            marks=[AttendanceMarkInput(student_user_id=str(student_id), status=AttendanceMarkStatus.ABSENT)]
        ),
    )
    with pytest.raises(AppError) as exc:
        await submit_attendance(
            scope,
            user,
            PydanticObjectId(created.id),
            AttendanceSubmitPayload(
                marks=[AttendanceMarkInput(student_user_id=str(student_id), status=AttendanceMarkStatus.PRESENT)]
            ),
        )
    assert exc.value.code == "CONFLICT"


@pytest.mark.anyio
async def test_unauthorized_class_access(db_ready) -> None:
    scope, user, _, _, _ = await _faculty_seed()
    with pytest.raises(AppError) as exc:
        await create_attendance_session(
            scope,
            user,
            AttendanceSessionCreate(course_code="CS999", section="A", session_date=date.today()),
        )
    assert exc.value.code == "FORBIDDEN"


def test_attendance_percentage_rules() -> None:
    rules = AttendancePolicyRules(min_percentage_required=75)
    records = [
        AttendanceRecord(
            tenant_id=PydanticObjectId(),
            session_id=PydanticObjectId(),
            student_user_id=PydanticObjectId(),
            status=AttendanceMarkStatus.PRESENT,
        ),
        AttendanceRecord(
            tenant_id=PydanticObjectId(),
            session_id=PydanticObjectId(),
            student_user_id=PydanticObjectId(),
            status=AttendanceMarkStatus.ABSENT,
        ),
    ]
    assert calculate_percentage(records, rules) == 50.0


@pytest.mark.anyio
async def test_attendance_shortages(db_ready) -> None:
    scope, user, tenant_id, course_id, student_id = await _faculty_seed()
    session = AttendanceSession(
        tenant_id=tenant_id,
        faculty_user_id=user.id,
        course_id=course_id,
        course_code="CS301",
        section="A",
        session_date=date.today(),
        academic_year_label="2025-26",
        semester_label="Odd",
        status=AttendanceSessionStatus.SUBMITTED,
        submitted_at=datetime.now(timezone.utc),
    )
    await session.insert()
    await AttendanceRecord(
        tenant_id=tenant_id,
        session_id=session.id,
        student_user_id=student_id,
        status=AttendanceMarkStatus.ABSENT,
    ).insert()
    shortages = await attendance_shortages(scope, user, "CS301", "A")
    assert len(shortages) >= 1


def test_invalid_file_rejected() -> None:
    with pytest.raises(AppError) as exc:
        lms_storage.validate_upload("malware.exe", "application/octet-stream", 100)
    assert exc.value.code == "VALIDATION_ERROR"


def test_valid_file_accepted() -> None:
    lms_storage.validate_upload("notes.pdf", "application/pdf", 1024)
    key, checksum = lms_storage.write_bytes(
        lms_storage.storage_key_for("tenant", "materials", "notes.pdf"),
        b"%PDF-1.4 test",
    )
    assert key
    assert len(checksum) == 64


@pytest.mark.anyio
async def test_assignment_publish_and_evaluate(db_ready) -> None:
    scope, user, tenant_id, course_id, student_id = await _faculty_seed()
    rule = AssignmentRule(tenant_id=tenant_id, resubmission_allowed=True, max_resubmissions=1)
    await rule.insert()
    created = await create_lms_assignment(
        scope,
        user,
        LmsAssignmentCreate(
            course_code="CS301",
            section="A",
            title="Assignment 1",
            instructions="Solve all",
            max_marks=20,
            deadline_at=datetime.now(timezone.utc) + timedelta(days=2),
        ),
    )
    published = await publish_lms_assignment(scope, user, PydanticObjectId(created.id))
    assert published.status == LmsAssignmentStatus.PUBLISHED
    assignment = await CourseAssignment.get(PydanticObjectId(created.id))
    assert assignment is not None
    submission = AssignmentSubmission(
        tenant_id=tenant_id,
        assignment_id=assignment.id,
        student_user_id=student_id,
        status="submitted",
        submitted_at=datetime.now(timezone.utc),
        file_name="work.pdf",
    )
    await submission.insert()
    result = await evaluate_submission(
        scope,
        user,
        submission.id,
        EvaluationCreate(marks_awarded=18, feedback="Good work"),
    )
    assert result.marks_awarded == 18
