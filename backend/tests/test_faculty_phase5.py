"""Faculty phase 5 — communication and self-service."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from beanie import PydanticObjectId

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.academics.curriculum_models import CourseRecord, EnrollmentRosterEntry
from app.modules.faculty.communication_schemas import AnnouncementCreate
from app.modules.faculty.communication_service import create_announcement, publish_announcement
from app.modules.faculty.enums import AssignmentRole, AssignmentStatus
from app.modules.faculty.models import FacultyAssignment
from app.modules.faculty.self_service_schemas import LeaveRequestCreate
from app.modules.faculty.self_service_service import get_employment_info, list_payslips, submit_leave
from app.modules.auth.models import User
from app.modules.hr.models import PayslipReference
from app.modules.tenants.models import Department, Tenant


@pytest.fixture
async def db_ready():
    try:
        await connect_to_mongo()
        await connect_redis()
    except Exception as exc:
        pytest.skip(f"Dependencies not available: {exc}")
    for model in document_models():
        await model.get_motor_collection().delete_many({})
    yield
    await close_redis()
    await close_mongo()


async def _seed() -> tuple[AccessScope, User, str]:
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"C5 {suffix}", code=f"c5_{suffix}")
    await tenant.insert()
    dept = Department(tenant_id=tenant.id, name="CSE", code="CSE")
    await dept.insert()
    faculty = User(
        email=f"f5+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Faculty 5",
        role=Role.FACULTY,
        tenant_id=tenant.id,
        department_id=dept.id,
    )
    await faculty.insert()
    student = User(
        email=f"s5+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()
    course = CourseRecord(
        tenant_id=tenant.id,
        course_id=f"cid5-{suffix}",
        course_code="CS501",
        name="AI Lab",
        credit_units=2,
    )
    await course.insert()
    await FacultyAssignment(
        tenant_id=tenant.id,
        user_id=faculty.id,
        course_id=course.course_id,
        course_code="CS501",
        course_name="AI Lab",
        section="A",
        academic_year_label="2025-26",
        semester_label="Odd",
        assignment_role=AssignmentRole.PRIMARY,
        status=AssignmentStatus.ACTIVE,
    ).insert()
    await EnrollmentRosterEntry(
        tenant_id=tenant.id,
        course_id=course.course_id,
        course_code="CS501",
        section_code="A",
        student_user_id=student.id,
        roll_number="23CS501",
        display_name="Student",
        academic_year_label="2025-26",
        semester_label="Odd",
    ).insert()
    scope = AccessScope(
        role=Role.FACULTY,
        user_id=faculty.id,
        tenant_id=tenant.id,
        department_id=dept.id,
        effective_permissions=permissions_for_role(Role.FACULTY),
    )
    return scope, faculty, suffix


@pytest.mark.anyio
async def test_announcement_publish_with_section_auth(db_ready) -> None:
    scope, user, _ = await _seed()
    created = await create_announcement(
        scope,
        user,
        AnnouncementCreate(course_code="CS501", section="A", title="Test", body="Hello class"),
    )
    published = await publish_announcement(scope, user, PydanticObjectId(created.id))
    assert published.status == "published"


@pytest.mark.anyio
async def test_unauthorized_course_announcement(db_ready) -> None:
    scope, user, _ = await _seed()
    with pytest.raises(AppError) as exc:
        await create_announcement(
            scope,
            user,
            AnnouncementCreate(course_code="CS999", title="X", body="Y"),
        )
    assert exc.value.code == "FORBIDDEN"


@pytest.mark.anyio
async def test_leave_request_submission(db_ready) -> None:
    scope, user, _ = await _seed()
    start = date.today() + timedelta(days=3)
    end = start + timedelta(days=1)
    req = await submit_leave(
        scope,
        user,
        LeaveRequestCreate(start_date=start, end_date=end, reason="Family event travel"),
    )
    assert req.status == "submitted"


@pytest.mark.anyio
async def test_payslip_unavailable_without_integration(db_ready) -> None:
    scope, user, _ = await _seed()
    result = await list_payslips(scope, user)
    assert result.status == "unavailable"


@pytest.mark.anyio
async def test_payslip_owner_only(db_ready) -> None:
    from app.modules.faculty.self_service_service import download_payslip

    scope, user, suffix = await _seed()
    other = User(
        email=f"other5+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Other Faculty",
        role=Role.FACULTY,
        tenant_id=scope.tenant_id,
    )
    await other.insert()
    from app.modules.lms import storage as lms_storage

    key, _ = lms_storage.write_bytes(
        lms_storage.storage_key_for(str(scope.tenant_id), "payslips", "p.pdf"),
        b"%PDF",
    )
    slip = PayslipReference(
        tenant_id=scope.tenant_id,
        employee_user_id=user.id,
        period_label="2025-10",
        storage_key=key,
    )
    await slip.insert()
    with pytest.raises(AppError) as exc:
        other_scope = AccessScope(
            role=Role.FACULTY,
            user_id=other.id,
            tenant_id=scope.tenant_id,
            department_id=None,
            effective_permissions=permissions_for_role(Role.FACULTY),
        )
        await download_payslip(other_scope, other, slip.id)
    assert exc.value.code == "NOT_FOUND"


@pytest.mark.anyio
async def test_employment_not_configured(db_ready) -> None:
    scope, user, _ = await _seed()
    info = await get_employment_info(scope, user)
    assert info.status in {"not_configured", "partial"}


def test_report_download_url_includes_signature() -> None:
    from datetime import timedelta

    from app.common.time import utcnow
    from app.modules.faculty.report_tokens import hash_token, issue_token, sign_download

    export_id = "507f1f77bcf86cd799439011"
    tenant_id = "507f1f77bcf86cd799439012"
    user_id = "507f1f77bcf86cd799439013"
    raw = issue_token()
    expires = utcnow() + timedelta(hours=1)
    sig = sign_download(
        export_id=export_id,
        tenant_id=tenant_id,
        user_id=user_id,
        expires_at=expires,
        raw=raw,
    )
    assert len(sig) == 64
    assert hash_token(raw) != raw
