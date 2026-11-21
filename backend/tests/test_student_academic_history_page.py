"""Student academic history page."""

from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.student_academic_history_page_service import get_student_academic_history_page
from app.modules.college_admin.student_admin_models import StudentLifecycleStatus, StudentRecord
from app.modules.students.enums import AcademicStanding, ProgressionStatus, StudentEnrollmentStatus
from app.modules.students.models import StudentAcademicRecord
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
async def test_academic_history_page_builds_rows(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"College HIST {suffix}", code=f"hist_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+hist+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="College Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    student = User(
        email=f"aarav+hist+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Aarav Menon",
        role=Role.STUDENT,
        tenant_id=tenant.id,
        is_active=True,
    )
    await student.insert()
    record = StudentRecord(
        tenant_id=tenant.id,
        user_id=student.id,
        roll_number=f"22CS{suffix[:4]}",
        programme_code="CSE",
        batch_label="2022",
        section_code="A",
        lifecycle_status=StudentLifecycleStatus.ACTIVE,
    )
    await record.insert()
    await StudentAcademicRecord(
        tenant_id=tenant.id,
        user_id=student.id,
        academic_year_label="2025-26",
        semester_label="semester-4",
        enrollment_status=StudentEnrollmentStatus.COMPLETED,
        academic_standing=AcademicStanding.GOOD,
        progression_status=ProgressionStatus.PROMOTED,
        credits_earned=24,
        cgpa=8.74,
        eligibility_summary={"sgpa": 8.92, "attendance_percent": 93},
    ).insert()

    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    page = await get_student_academic_history_page(scope, record_id=str(record.id))
    assert page.page_title == "Student Academic History"
    assert page.profile_name == "Aarav Menon"
    assert len(page.semester_rows) == 1
    assert page.semester_rows[0].result_label == "Pass"
    assert "CGPA" in page.semester_footer_label