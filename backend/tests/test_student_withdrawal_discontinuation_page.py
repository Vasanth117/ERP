"""Student withdrawal / discontinuation workflow page."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.schemas import StudentWithdrawalSubmitPayload
from app.modules.college_admin.student_admin_models import (
    StudentLifecycleStatus,
    StudentRecord,
    StudentWithdrawalWorkflowStatus,
)
from app.modules.college_admin.student_withdrawal_discontinuation_page_service import (
    get_student_withdrawal_discontinuation_page,
    submit_student_withdrawal_for_approval,
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


@pytest.mark.anyio
async def test_withdrawal_page_creates_draft(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"College WDL {suffix}", code=f"wdl_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+wdl+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="College Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    dept_id = tenant.id
    student = User(
        email=f"student+wdl+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Lakshmi N",
        role=Role.STUDENT,
        tenant_id=tenant.id,
        is_active=True,
    )
    await student.insert()
    record = StudentRecord(
        tenant_id=tenant.id,
        user_id=student.id,
        roll_number=f"24CE{suffix[:4].upper()}",
        programme_code="CSE",
        batch_label="2024",
        department_id=dept_id,
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
    page = await get_student_withdrawal_discontinuation_page(scope, record_id=str(record.id))
    assert "Lakshmi N" in page.student_line
    assert len(page.clearance_rows) == 4
    assert page.can_submit is True

    submitted = await submit_student_withdrawal_for_approval(
        scope,
        StudentWithdrawalSubmitPayload(
            record_id=str(record.id),
            request_id=page.request_id,
            withdrawal_type="withdrawal",
            reason="Moving to another city",
            last_attendance_date="2026-10-31",
        ),
    )
    assert submitted.can_submit is False
    assert submitted.wizard_steps[0].key == "request"

    record = await StudentRecord.get(record.id)
    assert record.lifecycle_status in (StudentLifecycleStatus.ACTIVE, StudentLifecycleStatus.WITHDRAWN)
    if submitted.active_step_key == "certificates":
        assert record.lifecycle_status == StudentLifecycleStatus.WITHDRAWN