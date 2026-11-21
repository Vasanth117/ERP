"""Student administration dashboard page (CA 06.01)."""

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
from app.modules.college_admin.student_admin_models import AdmissionStatus, StudentAdmission
from app.modules.college_admin.student_administration_dashboard_page_service import (
    get_student_administration_dashboard_page,
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


async def _seed_admin(suffix: str) -> tuple[Tenant, User, AccessScope]:
    tenant = Tenant(name=f"College SA {suffix}", code=f"sa_{suffix}")
    await tenant.insert()
    user = User(
        email=f"admin+sa+{suffix}@example.com",
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
    return tenant, user, scope


@pytest.mark.anyio
async def test_student_administration_dashboard_page_metrics(db_ready):
    suffix = uuid4().hex[:8]
    tenant, _user, scope = await _seed_admin(suffix)
    year = AcademicYear(
        tenant_id=tenant.id,
        year_code="2026-27",
        label="2026-27",
        is_current=True,
    )
    await year.insert()
    admission = StudentAdmission(
        tenant_id=tenant.id,
        admission_number=f"ADM-{suffix}",
        applicant_name="Rohan Mehta",
        applicant_email=f"rohan+{suffix}@example.com",
        programme_code="CSE",
        academic_year_code="2026-27",
        status=AdmissionStatus.CONFIRMED,
        metadata={"category": "government", "documents_verified": True},
    )
    await admission.insert()

    page = await get_student_administration_dashboard_page(scope, academic_year_code="2026-27")
    assert page.page_title == "Student Administration Dashboard"
    assert any(k.key == "admissions_year" and k.value == "1" for k in page.kpis)
    assert len(page.recent_admissions_rows) == 1
    assert page.recent_admissions_rows[0].student_name == "Rohan Mehta"