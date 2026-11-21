"""Batch & section allocation page (Students tab)."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.batch_section_allocation_page_service import (
    auto_allocate_batch_section_allocation,
    get_batch_section_allocation_page,
)
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.modules.college_admin.student_admin_models import StudentLifecycleStatus, StudentRecord
from app.modules.department_admin.models import (
    DepartmentBatch,
    DepartmentBatchStatus,
    DepartmentSection,
    DepartmentSectionStatus,
)
from beanie.odm.operators.find.comparison import Eq

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


async def _seed(suffix: str) -> tuple[AccessScope, StudentRecord, DepartmentSection]:
    tenant = Tenant(name=f"College Sec {suffix}", code=f"sec_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+sec+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="College Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    dept = InstitutionDepartment(tenant_id=tenant.id, name="CSE", department_code="CSE")
    await dept.insert()
    central_id = dept.central_department_id or dept.id

    student = User(
        email=f"student+sec+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Kabir Sharma",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()

    batch = DepartmentBatch(
        tenant_id=tenant.id,
        institution_department_id=dept.id,
        central_department_id=central_id,
        programme_code="CSE",
        batch_label="2026 batch",
        status=DepartmentBatchStatus.ACTIVE,
    )
    await batch.insert()

    section = DepartmentSection(
        tenant_id=tenant.id,
        department_batch_id=batch.id,
        central_department_id=central_id,
        section_code="A",
        name="Section A",
        capacity=65,
        status=DepartmentSectionStatus.ACTIVE,
    )
    await section.insert()

    record = StudentRecord(
        tenant_id=tenant.id,
        user_id=student.id,
        roll_number=f"26EC{suffix[:4]}",
        programme_code="CSE",
        batch_label="2026 batch",
        lifecycle_status=StudentLifecycleStatus.ACTIVE,
        department_id=dept.id,
    )
    await record.insert()

    profile = StudentProfile(
        tenant_id=tenant.id,
        user_id=student.id,
        programme_code="CSE",
        batch_label="2026 batch",
        department_id=central_id,
        roll_number=record.roll_number,
    )
    await profile.insert()

    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    return scope, record, section


@pytest.mark.anyio
async def test_batch_section_allocation_page_lists_section_and_unallocated(db_ready):
    suffix = uuid4().hex[:8]
    scope, record, section = await _seed(suffix)
    page = await get_batch_section_allocation_page(scope)
    assert page.page_title == "Batch & Section Allocation"
    assert any(row.section_id == str(section.id) for row in page.section_rows)
    assert any(row.record_id == str(record.id) for row in page.unallocated_rows)


@pytest.mark.anyio
async def test_auto_allocate_assigns_section(db_ready):
    suffix = uuid4().hex[:8]
    scope, record, section = await _seed(suffix)
    updated = await auto_allocate_batch_section_allocation(scope)
    assert not any(row.record_id == str(record.id) for row in updated.unallocated_rows)
    profile = await StudentProfile.find_one(
        Eq(StudentProfile.tenant_id, record.tenant_id),
        Eq(StudentProfile.user_id, record.user_id),
    )
    assert profile and profile.section_code == "A"