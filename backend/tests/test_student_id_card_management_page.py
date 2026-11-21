"""Student ID card management page."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.schemas import StudentIdCardIssuePayload
from app.modules.college_admin.student_admin_models import (
    StudentIdCard,
    StudentIdCardStatus,
    StudentLifecycleStatus,
    StudentRecord,
)
from app.modules.college_admin.student_id_card_management_page_service import (
    get_student_id_card_management_page,
    issue_student_id_card,
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


@pytest.mark.anyio
async def test_id_card_page_and_issue(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"College IDC {suffix}", code=f"NCE{suffix[:2]}")
    await tenant.insert()
    admin = User(
        email=f"admin+idc+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="College Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    student = User(
        email=f"student+idc+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Aarav Menon",
        role=Role.STUDENT,
        tenant_id=tenant.id,
        is_active=True,
    )
    await student.insert()
    record = StudentRecord(
        tenant_id=tenant.id,
        user_id=student.id,
        roll_number=f"22{suffix[:4].upper()}",
        programme_code="CSE",
        batch_label="2022",
        lifecycle_status=StudentLifecycleStatus.ACTIVE,
    )
    await record.insert()

    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    page = await get_student_id_card_management_page(scope)
    assert page.page_title == "Student ID Card Management"
    assert len(page.kpis) == 4
    assert page.kpis[0].key == "issued"
    assert any(row.student_name == "Aarav Menon" for row in page.card_rows)
    pending = next(row for row in page.card_rows if row.student_name == "Aarav Menon")
    assert pending.card_number_label == "Not issued"
    assert pending.status_label == "Pending print"

    after_issue = await issue_student_id_card(
        scope,
        StudentIdCardIssuePayload(record_id=str(record.id)),
    )
    issued_row = next(row for row in after_issue.card_rows if row.student_name == "Aarav Menon")
    assert issued_row.card_number_label != "Not issued"
    assert issued_row.status_label in ("Active", "Renewal due")

    from beanie.odm.operators.find.comparison import Eq

    card = await StudentIdCard.find_one(Eq(StudentIdCard.student_record_id, record.id))
    assert card is not None
    assert card.status == StudentIdCardStatus.ACTIVE