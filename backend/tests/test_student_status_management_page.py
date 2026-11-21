"""Student status management page."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.schemas import StudentStatusChangeSubmitPayload
from app.modules.college_admin.student_admin_models import (
    StudentLifecycleStatus,
    StudentRecord,
    StudentStatusChangeApproval,
    StudentStatusChangeRequest,
)
from app.modules.college_admin.student_status_management_page_service import (
    approve_student_status_change,
    get_student_status_management_page,
    submit_student_status_change,
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
async def test_status_management_page_empty_tenant(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"College STS {suffix}", code=f"sts_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+sts+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="College Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    page = await get_student_status_management_page(scope)
    assert page.page_title == "Student Status Management"
    assert len(page.status_mix_items) == 4
    assert page.status_mix_items[0].count == 0
    assert page.status_change_rows == []


@pytest.mark.anyio
async def test_submit_and_approve_status_change(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"College STS2 {suffix}", code=f"sts2_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+sts2+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="College Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    student = User(
        email=f"student+sts2+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Rohan Iyer",
        role=Role.STUDENT,
        tenant_id=tenant.id,
        is_active=True,
    )
    await student.insert()
    record = StudentRecord(
        tenant_id=tenant.id,
        user_id=student.id,
        roll_number=f"21ME{suffix[:4].upper()}",
        programme_code="MECH",
        batch_label="2021",
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
    after_submit = await submit_student_status_change(
        scope,
        StudentStatusChangeSubmitPayload(
            record_id=str(record.id),
            new_status_bucket="on_hold",
            reason="Fee dues > 60 days",
        ),
    )
    assert len(after_submit.status_change_rows) == 1
    assert after_submit.status_change_rows[0].approval_status_label == "Pending"
    request_id = after_submit.status_change_rows[0].request_id

    after_approve = await approve_student_status_change(scope, request_id=request_id)
    assert after_approve.status_change_rows[0].approval_status_label == "Approved"

    doc = await StudentStatusChangeRequest.get(request_id)
    assert doc.approval_status == StudentStatusChangeApproval.APPROVED

    record = await StudentRecord.get(record.id)
    assert record.lifecycle_status == StudentLifecycleStatus.ON_LEAVE

    page = await get_student_status_management_page(scope)
    on_hold = next(i for i in page.status_mix_items if i.status_key == "on_hold")
    assert on_hold.count == 1