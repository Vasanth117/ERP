"""Examination dashboard overview page (CA 09.01)."""

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
from app.modules.college_admin.examination_dashboard_page_service import get_examination_dashboard_page
from app.modules.examinations.exam_cell_enums import ExamSessionStatus, ExamSessionType
from app.modules.examinations.exam_cell_models import ExamSession
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
async def test_examination_dashboard_page_structure(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"College Exam Dash {suffix}", code=f"exd_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+exdash+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Exam Office",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    now = utcnow()
    session = ExamSession(
        tenant_id=tenant.id,
        session_id=f"SES-D-{suffix}",
        session_code=f"END-{suffix}",
        name="Nov/Dec End Semester",
        examination_type=ExamSessionType.REGULAR,
        academic_year_label="2025-26",
        semester_label="Odd",
        registration_start_at=now - timedelta(days=5),
        registration_end_at=now + timedelta(days=20),
        examination_start_at=now + timedelta(days=30),
        examination_end_at=now + timedelta(days=45),
        status=ExamSessionStatus.REGISTRATION_OPEN,
    )
    await session.insert()
    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    page = await get_examination_dashboard_page(scope)
    assert page.page_title == "Examination Dashboard"
    assert len(page.workflow_steps) == 6
    assert len(page.kpis) == 4
    assert any(row.session_id == session.session_id for row in page.session_rows)