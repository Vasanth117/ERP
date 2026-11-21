"""Attendance correction requests and approval pages (CA 08.08 / 08.09)."""

from datetime import date
from uuid import uuid4

from app.common.time import utcnow

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.attendance.enums import AttendanceCorrectionStatus, AttendanceMarkStatus, AttendanceSessionStatus
from app.modules.attendance.models import AttendanceCorrectionRequest, AttendanceRecord, AttendanceSession
from app.modules.auth.models import User
from app.modules.college_admin.attendance_corrections_page_service import (
    get_attendance_approval_page,
    get_attendance_correction_requests_page,
)
from app.modules.college_admin.faculty_admin_models import FacultyRecord
from app.modules.college_admin.identity_models import DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.models import InstitutionSettings
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


@pytest.mark.anyio
async def test_attendance_correction_pages_shape(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"College AC {suffix}", code=f"ac_{suffix}")
    await tenant.insert()
    dept = InstitutionDepartment(
        tenant_id=tenant.id,
        department_code="ECE",
        name="Electronics and Communication",
        status=DepartmentStatus.ACTIVE,
    )
    await dept.insert()
    faculty_user = User(
        email=f"faculty+ac+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Dr. S. Hari",
        role=Role.FACULTY,
        tenant_id=tenant.id,
    )
    await faculty_user.insert()
    admin = User(
        email=f"admin+ac+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="College Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    await FacultyRecord(
        tenant_id=tenant.id,
        user_id=faculty_user.id,
        department_id=dept.id,
    ).insert()
    await InstitutionSettings(tenant_id=tenant.id, settings={"attendance_correction_requires_college_approval": True}).insert()

    session = AttendanceSession(
        tenant_id=tenant.id,
        faculty_user_id=faculty_user.id,
        course_id="dsp",
        course_code="DSP",
        section="ECE 5A",
        session_date=date(2026, 11, 5),
        academic_year_label="2026",
        semester_label="Sem-1",
        status=AttendanceSessionStatus.SUBMITTED,
    )
    await session.insert()
    student_user = User(
        email=f"student+ac+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student_user.insert()
    await AttendanceRecord(
        tenant_id=tenant.id,
        session_id=session.id,
        student_user_id=student_user.id,
        status=AttendanceMarkStatus.ABSENT,
    ).insert()

    correction = AttendanceCorrectionRequest(
        tenant_id=tenant.id,
        faculty_user_id=faculty_user.id,
        session_id=session.id,
        student_user_id=student_user.id,
        requested_status=AttendanceMarkStatus.PRESENT,
        reason="Marked in wrong section",
        status=AttendanceCorrectionStatus.PENDING,
        department_endorsed_at=utcnow(),
    )
    await correction.insert()

    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )

    listing = await get_attendance_correction_requests_page(scope)
    assert listing.page_title == "Attendance Correction Requests"
    assert len(listing.kpis) == 3

    approval = await get_attendance_approval_page(scope, request_id=str(correction.id))
    assert approval.page_title == "Attendance Approval"
    assert approval.faculty_label == "Dr. S. Hari"
    assert approval.class_label == "DSP · ECE 5A"
    assert approval.reason_text == "Marked in wrong section"
    assert len(approval.approval_steps) >= 2
    assert approval.can_decide is True