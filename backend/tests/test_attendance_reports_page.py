"""Attendance reports page (CA 08.12)."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.attendance_reports_page_service import (
    create_attendance_report,
    get_attendance_reports_page,
)
from app.modules.college_admin.schemas import AttendanceReportCreate
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
async def test_attendance_reports_page_shape(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"College REP {suffix}", code=f"rep_{suffix}")
    await tenant.insert()
    user = User(
        email=f"admin+rep+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="College Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await user.insert()
    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=user.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )

    page = await get_attendance_reports_page(scope)
    assert page.page_title == "Attendance Reports"
    assert len(page.reports_table_headers) == 5
    assert page.report_rows
    assert "of" in page.reports_table_footer_label

    updated = await create_attendance_report(scope, AttendanceReportCreate(template_key="custom_summary"))
    assert updated.create_report_templates