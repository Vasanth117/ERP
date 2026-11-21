"""Faculty / employee history (CA 07.13)."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import FacultyEmploymentHistory
from app.modules.college_admin.faculty_employee_history_page_service import get_faculty_employee_history_page
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


async def _scope(suffix: str) -> tuple[Tenant, User, AccessScope]:
    tenant = Tenant(name=f"College FEH {suffix}", code=f"feh_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+feh+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="College Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    staff = User(
        email=f"staff+feh+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Dr. Nisha Varma",
        role=Role.FACULTY,
        tenant_id=tenant.id,
    )
    await staff.insert()
    await FacultyEmploymentHistory(
        tenant_id=tenant.id,
        user_id=staff.id,
        event_type="status_review",
        note="Status review submitted",
        actor_id=admin.id,
    ).insert()
    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    return tenant, staff, scope


@pytest.mark.anyio
async def test_faculty_employee_history_page_loads(db_ready):
    _, staff, scope = await _scope(uuid4().hex[:8])
    page = await get_faculty_employee_history_page(scope)
    assert page.page_title == "Faculty / Employee History"
    assert page.table_headers[1] == "Employee"
    assert len(page.history_rows) == 1
    assert page.history_rows[0].employee_name == staff.full_name
    assert page.history_rows[0].change_label == "Status review submitted"