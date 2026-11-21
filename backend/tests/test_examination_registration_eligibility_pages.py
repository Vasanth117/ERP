"""Student exam eligibility & hall ticket administration pages (CA 09.04–09.06)."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.hall_ticket_administration_page_service import get_hall_ticket_administration_page
from app.modules.college_admin.student_exam_eligibility_page_service import get_student_exam_eligibility_page
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


def _admin_scope(tenant: Tenant, admin: User) -> AccessScope:
    return AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )


@pytest.mark.anyio
async def test_student_exam_eligibility_page_empty(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"College Elig {suffix}", code=f"el_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+elig+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Exam Office",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    page = await get_student_exam_eligibility_page(_admin_scope(tenant, admin))
    assert page.page_title == "Student Exam Eligibility"
    assert page.ineligible_rows == []
    assert any(item.active for item in page.sub_nav)
    assert page.kpis[0].key == "eligible"


@pytest.mark.anyio
async def test_hall_ticket_administration_page_empty(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"College HT {suffix}", code=f"ht_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+ht+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Exam Office",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    page = await get_hall_ticket_administration_page(_admin_scope(tenant, admin))
    assert page.page_title == "Hall Ticket Administration"
    assert page.ticket_rows == []
    assert any(item.key == "hall_tickets" and item.active for item in page.sub_nav)