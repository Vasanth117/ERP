"""Student admission list page (Admissions tab)."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.student_admission_page_service import get_student_admission_page
from app.modules.college_admin.student_admin_models import AdmissionStatus, StudentAdmission
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
    tenant = Tenant(name=f"College ADM {suffix}", code=f"adm_{suffix}")
    await tenant.insert()
    user = User(
        email=f"admin+adm+{suffix}@example.com",
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
async def test_student_admission_page_lists_application(db_ready):
    suffix = uuid4().hex[:8]
    tenant, scope = await _seed_admin(suffix)
    ay = "2026-27"

    admission = StudentAdmission(
        tenant_id=tenant.id,
        admission_number=f"ADM-{suffix[:4].upper()}",
        applicant_name="Sneha Pillai",
        applicant_email=f"sneha+{suffix}@example.com",
        programme_code="CSE",
        academic_year_code=ay,
        status=AdmissionStatus.CONFIRMED,
        metadata={"category": "general", "marks_percentage": 96.4},
    )
    await admission.insert()

    page = await get_student_admission_page(scope, academic_year_code=ay)
    assert page.page_title == "Student Admission"
    assert len(page.applications) == 1
    assert page.applications[0].applicant_name == "Sneha Pillai"
    assert page.applications[0].status_label == "Approved"
    assert page.kpis[0].value == "1"


@pytest.mark.anyio
async def test_student_admission_page_filters_pending_docs(db_ready):
    suffix = uuid4().hex[:8]
    tenant, scope = await _seed_admin(suffix)

    admission = StudentAdmission(
        tenant_id=tenant.id,
        admission_number=f"ADM2-{suffix[:4].upper()}",
        applicant_name="Kabir Sharma",
        applicant_email=f"kabir+{suffix}@example.com",
        programme_code="ECE",
        academic_year_code="2026-27",
        status=AdmissionStatus.PENDING,
        metadata={"category": "management", "pending_documents_count": 2, "marks_percentage": 91.2},
    )
    await admission.insert()

    page = await get_student_admission_page(scope, status_filter="documents_pending")
    assert len(page.applications) == 1
    assert page.applications[0].status_label == "Documents pending"