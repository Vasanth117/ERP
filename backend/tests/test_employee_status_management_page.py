"""Employee status management (CA 07.12)."""

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
from app.modules.college_admin.employee_status_management_page_service import (
    approve_employee_status_change,
    get_employee_status_management_page,
    submit_employee_status_change,
)
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.college_admin.schemas import EmployeeStatusChangeSubmitPayload
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


async def _scope(suffix: str) -> tuple[Tenant, EmployeeRecord, AccessScope]:
    tenant = Tenant(name=f"College ESM {suffix}", code=f"esm_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+esm+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="College Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    staff = User(
        email=f"staff+esm+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Dr. Nisha Varma",
        role=Role.FACULTY,
        tenant_id=tenant.id,
    )
    await staff.insert()
    employee = EmployeeRecord(
        tenant_id=tenant.id,
        user_id=staff.id,
        employee_id="EMP-1001",
        employment_status=FacultyEmploymentStatus.PROBATION,
        employment_type="permanent",
    )
    await employee.insert()
    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    return tenant, employee, scope


@pytest.mark.anyio
async def test_employee_status_management_page_loads(db_ready):
    _, employee, scope = await _scope(uuid4().hex[:8])
    page = await get_employee_status_management_page(scope)
    assert page.page_title == "Employee Status Management"
    assert len(page.status_mix_items) == 4
    assert page.status_mix_items[1].count >= 1
    assert any(opt.record_id == str(employee.id) for opt in page.employee_picker_options)


@pytest.mark.anyio
async def test_employee_status_submit_and_approve(db_ready):
    _, employee, scope = await _scope(uuid4().hex[:8])
    submitted = await submit_employee_status_change(
        scope,
        EmployeeStatusChangeSubmitPayload(
            record_id=str(employee.id),
            new_status=FacultyEmploymentStatus.CONFIRMED.value,
            reason="Probation review passed",
            effective_date=utcnow().date(),
        ),
    )
    assert len(submitted.status_change_rows) == 1
    assert submitted.status_change_rows[0].approval_status_label == "Pending"
    request_id = submitted.status_change_rows[0].request_id
    approved = await approve_employee_status_change(scope, request_id=request_id)
    row = next(r for r in approved.status_change_rows if r.request_id == request_id)
    assert row.approval_status_label == "Approved"
    refreshed = await EmployeeRecord.get(employee.id)
    assert refreshed.employment_status == FacultyEmploymentStatus.CONFIRMED