"""Institution academic year configuration save."""

from datetime import date
from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicYear
from app.modules.college_admin.institution_academic_year_page_service import (
    get_academic_year_configuration_page,
    save_academic_year_configuration,
)
from app.modules.college_admin.schemas import AcademicYearConfigurationSave, AcademicYearSemesterForm
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
async def test_save_academic_year_configuration_updates_table_and_timeline(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"College AY {suffix}", code=f"ay_{suffix}")
    await tenant.insert()
    user = User(
        email=f"admin+ay+{suffix}@example.com",
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
        label="New academic year",
        year_code=f"AY-{suffix}",
        is_current=True,
    )
    await year.insert()

    result = await save_academic_year_configuration(
        scope,
        year.id,
        AcademicYearConfigurationSave(
            semester_form=AcademicYearSemesterForm(
                odd_semester_start=date(2025, 7, 1),
                odd_semester_end=date(2025, 11, 30),
                even_semester_start=date(2026, 1, 2),
                even_semester_end=date(2026, 5, 15),
                year_end_closing=date(2026, 5, 31),
            ),
        ),
    )
    row = next(r for r in result.academic_years if r.year_id == str(year.id))
    assert row.start_label != "—"
    assert row.end_label != "—"
    assert "Odd" in row.semesters_label
    assert len(result.timeline) >= 2
    assert result.cancel_label == "Cancel"


@pytest.mark.anyio
async def test_save_academic_year_configuration_rejects_empty_semester_dates(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"College AY2 {suffix}", code=f"ay2_{suffix}")
    await tenant.insert()
    user = User(
        email=f"admin+ay2+{suffix}@example.com",
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
    year = AcademicYear(tenant_id=tenant.id, label="Draft year", year_code=f"AY2-{suffix}")
    await year.insert()

    with pytest.raises(AppError) as exc:
        await save_academic_year_configuration(
            scope,
            year.id,
            AcademicYearConfigurationSave(
                semester_form=AcademicYearSemesterForm(
                    odd_semester_start=date(2025, 7, 1),
                    odd_semester_end=None,
                ),
            ),
        )
    assert exc.value.status_code == 422

    page = await get_academic_year_configuration_page(scope, selected_year_id=str(year.id))
    assert page.semester_form is not None