"""Student enrollment management page."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.schemas import StudentEnrollmentBulkEnrollPayload
from app.modules.college_admin.student_admin_models import StudentLifecycleStatus, StudentRecord
from app.modules.college_admin.student_enrollment_management_page_service import (
    bulk_enroll_students_for_term,
    get_student_enrollment_management_page,
)
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


async def _seed(suffix: str) -> tuple[Tenant, StudentRecord, AccessScope, str]:
    tenant = Tenant(name=f"College Enroll {suffix}", code=f"en_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+en+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Academics Office",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    student = User(
        email=f"student+en+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Aarav Menon",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()
    record = StudentRecord(
        tenant_id=tenant.id,
        user_id=student.id,
        roll_number=f"22CS{suffix[:4]}",
        programme_code="CSE",
        batch_label="2022",
        lifecycle_status=StudentLifecycleStatus.ACTIVE,
    )
    await record.insert()
    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    term_key = "2026-27::Odd"
    return tenant, record, scope, term_key


@pytest.mark.anyio
async def test_enrollment_management_page_lists_student(db_ready):
    suffix = uuid4().hex[:8]
    _, record, scope, term_key = await _seed(suffix)
    page = await get_student_enrollment_management_page(scope, term_key=term_key)
    assert page.page_title == "Student Enrollment Management"
    assert page.kpis[0].key == "eligible"
    assert any(row.record_id == str(record.id) for row in page.enrollment_rows)


@pytest.mark.anyio
async def test_bulk_enroll_marks_student_enrolled(db_ready):
    suffix = uuid4().hex[:8]
    _, record, scope, term_key = await _seed(suffix)
    updated = await bulk_enroll_students_for_term(
        scope,
        StudentEnrollmentBulkEnrollPayload(record_ids=[str(record.id)], term_key=term_key),
    )
    row = next(r for r in updated.enrollment_rows if r.record_id == str(record.id))
    assert row.enrollment_status_label == "Enrolled"