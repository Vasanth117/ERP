"""New student registration wizard page."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.new_student_registration_page_service import (
    get_new_student_registration_page,
    save_new_student_registration_draft,
)
from app.modules.college_admin.schemas import NewStudentRegistrationDraftUpdate
from app.modules.college_admin.student_admin_models import StudentAdmission
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


async def _seed_admin(suffix: str) -> tuple[Tenant, AccessScope]:
    tenant = Tenant(name=f"College Reg {suffix}", code=f"reg_{suffix}")
    await tenant.insert()
    user = User(
        email=f"admin+reg+{suffix}@example.com",
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
    return tenant, scope


@pytest.mark.anyio
async def test_new_student_registration_page_loads(db_ready):
    suffix = uuid4().hex[:8]
    tenant, scope = await _seed_admin(suffix)
    admission = StudentAdmission(
        tenant_id=tenant.id,
        admission_number=f"ADM-{suffix[:4].upper()}",
        applicant_name="Kabir Sharma",
        applicant_email=f"kabir+{suffix}@example.com",
        programme_code="ECE",
        academic_year_code="2026-27",
        metadata={"category": "management"},
    )
    await admission.insert()

    page = await get_new_student_registration_page(scope, admission_id=str(admission.id))
    assert page.page_title == "New Student Registration"
    assert page.form.full_name == "Kabir Sharma"
    assert page.current_step_key == "student_information"
    assert len(page.steps) == 6


@pytest.mark.anyio
async def test_new_student_registration_save_draft(db_ready):
    suffix = uuid4().hex[:8]
    tenant, scope = await _seed_admin(suffix)
    page = await get_new_student_registration_page(scope)
    updated = await save_new_student_registration_draft(
        scope,
        NewStudentRegistrationDraftUpdate(
            admission_id=page.admission_id,
            values={
                "full_name": "Anika Rao",
                "email": f"anika+{suffix}@example.com",
                "mobile": "+91 98400 77210",
            },
        ),
    )
    assert updated.form.full_name == "Anika Rao"
    assert updated.has_draft