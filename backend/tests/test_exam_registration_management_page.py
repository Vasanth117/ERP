"""Exam registration management page (CA 09.05)."""

from datetime import timedelta
from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.time import utcnow
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.exam_registration_management_page_service import (
    get_exam_registration_management_page,
)
from app.modules.examinations.exam_cell_enums import ExamSessionStatus, ExamSessionType
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_registration_enums import ExamRegistrationStatus
from app.modules.examinations.exam_cell_registration_models import ExamRegistration
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
async def test_exam_registration_management_page_empty_sessions(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"College Exam Reg {suffix}", code=f"ex_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+exreg+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Exam Office",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    page = await get_exam_registration_management_page(scope)
    assert page.page_title == "Exam Registration Management"
    assert page.registration_rows == []
    assert page.search_placeholder
    assert any(item.active for item in page.sub_nav)


@pytest.mark.anyio
async def test_exam_registration_management_page_lists_registration(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"College Exam Reg {suffix}", code=f"ex2_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+exreg2+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Exam Office",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    student = User(
        email=f"student+exreg+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Lakshmi Rao",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()
    now = utcnow()
    session = ExamSession(
        tenant_id=tenant.id,
        session_id=f"SES-{suffix}",
        session_code=f"SEM-{suffix}",
        name="Odd semester exams",
        examination_type=ExamSessionType.REGULAR,
        academic_year_label="2025-26",
        semester_label="Odd",
        registration_start_at=now - timedelta(days=3),
        registration_end_at=now + timedelta(days=10),
        examination_start_at=now + timedelta(days=20),
        examination_end_at=now + timedelta(days=30),
        status=ExamSessionStatus.REGISTRATION_OPEN,
    )
    await session.insert()
    reg = ExamRegistration(
        tenant_id=tenant.id,
        registration_id=f"REG-{suffix}",
        exam_session_id=session.id,
        student_user_id=student.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        status=ExamRegistrationStatus.SUBMITTED,
        fee_verified=True,
        submitted_at=now,
    )
    await reg.insert()
    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    page = await get_exam_registration_management_page(scope, session_id=session.session_id)
    assert page.kpis[0].key == "total"
    matched = next(row for row in page.registration_rows if row.registration_id == reg.registration_id)
    assert matched.eligibility_status_label
    assert matched.fee_status_label == "Paid"