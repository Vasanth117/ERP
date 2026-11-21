"""Department-wise and subject-wise attendance pages (CA 08.04/08.05)."""

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
from app.modules.college_admin.department_wise_attendance_page_service import get_department_wise_attendance_page
from app.modules.college_admin.subject_wise_attendance_page_service import get_subject_wise_attendance_page
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


async def _scope(suffix: str) -> AccessScope:
    tenant = Tenant(name=f"College DS {suffix}", code=f"ds_{suffix}")
    await tenant.insert()
    user = User(
        email=f"admin+ds+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="College Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await user.insert()
    return AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=user.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )


@pytest.mark.anyio
async def test_department_and_subject_pages(db_ready):
    suffix = uuid4().hex[:8]
    scope = await _scope(suffix)
    year = AcademicYear(
        tenant_id=scope.tenant_id,
        year_code="2026-27",
        label="2026-27",
        is_current=True,
    )
    await year.insert()

    dept_page = await get_department_wise_attendance_page(scope)
    assert dept_page.page_title == "Department-wise Attendance"
    assert dept_page.bars_section_title == "Average by department"

    subj_page = await get_subject_wise_attendance_page(scope)
    assert subj_page.page_title == "Subject-wise Attendance"
    assert subj_page.subjects_table_title == "Subjects"