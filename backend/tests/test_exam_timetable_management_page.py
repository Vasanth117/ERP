"""Exam timetable management page (CA 09.03)."""

from datetime import timedelta
from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.time import utcnow
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.exam_timetable_management_page_service import (
    get_exam_timetable_management_page,
    regenerate_exam_timetable_page,
)
from app.modules.college_admin.schemas import ExamTimetableManagementActionPayload
from app.modules.college_admin.student_admin_models import StudentRecord
from app.modules.examinations.exam_cell_enums import ExamSessionStatus, ExamSessionType
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_registration_enums import ExamRegistrationStatus
from app.modules.examinations.exam_cell_registration_models import ExamRegistration, ExamRegistrationSubject
from app.modules.students.models import StudentProfile
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
async def test_exam_timetable_management_page_and_regenerate(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"College Exam TT {suffix}", code=f"ext_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+extt+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Exam Office",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    student = User(
        email=f"stu+extt+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()
    await StudentProfile(tenant_id=tenant.id, user_id=student.id, full_name="Student").insert()
    await StudentRecord(
        tenant_id=tenant.id,
        user_id=student.id,
        programme_code="CSE",
        batch_label="2023",
        section_code="A",
    ).insert()
    now = utcnow()
    session = ExamSession(
        tenant_id=tenant.id,
        session_id=f"SES-TT-{suffix}",
        session_code=f"TT-{suffix}",
        name="Nov/Dec End Semester",
        examination_type=ExamSessionType.REGULAR,
        academic_year_label="2025-26",
        semester_label="Odd",
        registration_start_at=now - timedelta(days=5),
        registration_end_at=now + timedelta(days=20),
        examination_start_at=now + timedelta(days=30),
        examination_end_at=now + timedelta(days=45),
        status=ExamSessionStatus.REGISTRATION_OPEN,
    )
    await session.insert()
    registration_id = f"REG-{suffix}"
    await ExamRegistration(
        tenant_id=tenant.id,
        registration_id=registration_id,
        student_user_id=student.id,
        exam_session_id=session.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        status=ExamRegistrationStatus.CONFIRMED,
        fee_verified=True,
        submitted_at=now,
    ).insert()
    for code in ("CS3501", "CS3503"):
        await ExamRegistrationSubject(
            tenant_id=tenant.id,
            registration_id=registration_id,
            student_user_id=student.id,
            exam_session_id=session.id,
            course_code=code,
            subject_code=code,
        ).insert()

    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    page = await get_exam_timetable_management_page(scope, session_id=session.session_id)
    assert page.page_title == "Exam Timetable Management"
    assert page.selected_session_id == session.session_id

    regen = await regenerate_exam_timetable_page(
        scope,
        ExamTimetableManagementActionPayload(session_id=session.session_id),
    )
    assert regen.rows
    assert regen.clash_banner.visible