"""Attendance configuration pages (CA 08.10 / 08.11)."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.attendance_configuration_page_service import (
    get_attendance_configuration_page,
    get_attendance_rules_policies_page,
    save_attendance_configuration,
)
from app.modules.college_admin.schemas import AttendanceConfigurationSave
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
async def test_attendance_configuration_pages(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"College CFG {suffix}", code=f"cfg_{suffix}")
    await tenant.insert()
    user = User(
        email=f"admin+cfg+{suffix}@example.com",
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

    page = await get_attendance_configuration_page(scope)
    assert page.page_title == "Attendance Configuration"
    assert len(page.field_meta) == 4
    assert len(page.toggle_rules) == 3

    saved = await save_attendance_configuration(
        scope,
        AttendanceConfigurationSave(
            marking_window_key="same_day_18",
            correction_window_key="3_working_days",
            late_mark_after_key="15_minutes",
            session_length_key="60_minutes",
            toggle_rules={"allow_substitute_faculty": True, "lock_after_approval": True, "biometric_sync": False},
        ),
    )
    assert saved.marking_window_key == "same_day_18"

    policies = await get_attendance_rules_policies_page(scope)
    assert policies.page_title == "Attendance Rules & Policies"
    assert policies.policy_rows
    assert "of" in policies.policies_table_footer_label