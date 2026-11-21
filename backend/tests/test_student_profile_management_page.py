"""Student profile management page."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.schemas import StudentProfileManagementSavePayload
from app.modules.college_admin.student_admin_models import StudentLifecycleStatus, StudentRecord
from app.modules.college_admin.student_profile_management_page_service import (
    get_student_profile_management_page,
    save_student_profile_management,
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


async def _seed_student(suffix: str) -> tuple[Tenant, User, StudentRecord, AccessScope]:
    tenant = Tenant(name=f"College SPM {suffix}", code=f"spm_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+spm+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admissions Officer",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    student_user = User(
        email=f"student+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Aarav Menon",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student_user.insert()
    record = StudentRecord(
        tenant_id=tenant.id,
        user_id=student_user.id,
        roll_number=f"22CS{suffix[:4]}",
        programme_code="CSE",
        batch_label="2022-2026",
        section_code="A",
        contact_phone="+91 98400 11220",
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
    return tenant, student_user, record, scope


@pytest.mark.anyio
async def test_student_profile_management_page_loads(db_ready):
    suffix = uuid4().hex[:8]
    _, _, record, scope = await _seed_student(suffix)
    page = await get_student_profile_management_page(scope, str(record.id))
    assert page.page_title == "Student Profile Management"
    assert page.form.full_name == "Aarav Menon"
    assert len(page.locked_fields) == 2


@pytest.mark.anyio
async def test_student_profile_management_save(db_ready):
    suffix = uuid4().hex[:8]
    _, _, record, scope = await _seed_student(suffix)
    saved = await save_student_profile_management(
        scope,
        StudentProfileManagementSavePayload(
            record_id=str(record.id),
            values={
                "full_name": "Aarav Menon",
                "mobile": "+91 98400 99999",
                "email": f"student+{suffix}@example.com",
                "guardian_mobile": "+91 98410 55120",
                "address": "12, Lattice Bridge Road, Adyar, Chennai 600020",
                "reason_for_change": "Mobile number updated by student request",
            },
        ),
    )
    assert saved.form.mobile == "+91 98400 99999"