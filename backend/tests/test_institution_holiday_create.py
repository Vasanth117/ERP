"""Create institution calendar holiday."""

from datetime import date
from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicYear
from app.modules.college_admin.institution_calendar_page_service import (
    create_institution_holiday,
    get_institution_calendar_settings_page,
)
from app.modules.college_admin.schemas import InstitutionHolidayCreate
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
async def test_create_institution_holiday(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"College HL {suffix}", code=f"hl_{suffix}")
    await tenant.insert()
    user = User(
        email=f"admin+hl+{suffix}@example.com",
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
    year = AcademicYear(
        tenant_id=tenant.id,
        label="2025–26",
        year_code="2025-26",
        start_date=date(2025, 6, 1),
        end_date=date(2026, 5, 31),
        is_current=True,
    )
    await year.insert()

    result = await create_institution_holiday(
        scope,
        InstitutionHolidayCreate(
            academic_year_id=str(year.id),
            title="Republic Day",
            start_date=date(2026, 1, 26),
            holiday_type="national",
            applies_to="all",
        ),
    )
    assert result.holiday_id
    page = await get_institution_calendar_settings_page(scope, academic_year_id=str(year.id))
    assert page.holidays
    assert page.holidays[0].title == "Republic Day"