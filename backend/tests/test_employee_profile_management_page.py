"""Employee profile management page."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.employee_profile_management_page_service import (
    get_employee_profile_management_page,
    save_employee_profile_management,
)
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.college_admin.schemas import EmployeeProfileManagementSavePayload
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
async def test_employee_profile_management_save(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"College EPM {suffix}", code=f"epm_{suffix}")
    await tenant.insert()
    user = User(
        email=f"staff+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Dr. S. Hari",
        role=Role.HR_STAFF,
        tenant_id=tenant.id,
    )
    await user.insert()
    employee = EmployeeRecord(
        tenant_id=tenant.id,
        user_id=user.id,
        employee_id=f"EMP-{suffix[:4].upper()}",
        designation="Associate Professor",
        employment_type="permanent",
        employment_status=FacultyEmploymentStatus.ACTIVE,
        is_faculty=False,
        confidential_hr={"mobile": "+91 98400 22110"},
    )
    await employee.insert()

    admin = User(
        email=f"admin+epm+{suffix}@example.com",
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

    page = await get_employee_profile_management_page(scope, str(employee.id))
    assert page.page_title == "Employee Profile Management"
    assert page.profile_name == "Dr. S. Hari"

    updated = await save_employee_profile_management(
        scope,
        EmployeeProfileManagementSavePayload(
            record_id=str(employee.id),
            values={
                "full_name": "Dr. S. Hari",
                "mobile": "+91 98400 22111",
                "official_email": user.email,
                "emergency_contact": "Mrs. Hari - +91 98400 22111",
                "address": "7, Gandhi Road, Chennai",
                "reason_for_change": "Contact updated by employee",
            },
        ),
    )
    assert updated.phone_display == "+91 98400 22111"