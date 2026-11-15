"""Attendance submission eligibility (cancelled / rescheduled exclusion)."""

from datetime import date, datetime, time, timezone
from uuid import uuid4

import pytest

from beanie import PydanticObjectId

from app.core.database import close_mongo, connect_to_mongo
from app.core.redis import close_redis, connect_redis
from app.modules.academics.enums import SessionType, TimetableEntryStatus
from app.modules.academics.models import ClassSession, PendingAttendanceSubmission, TimetableEntry
from app.modules.department_admin.attendance_eligibility import filter_pending_requiring_submission, is_attendance_submission_expected
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
    from app.core.database import document_models

    for model in document_models():
        await model.get_motor_collection().delete_many({})
    yield
    await close_redis()
    await close_mongo()


@pytest.mark.anyio
async def test_cancelled_class_session_excluded(db_ready) -> None:
    tenant = Tenant(name="T", code=f"ae_{uuid4().hex[:6]}", institution_email="t@ex.com")
    await tenant.insert()
    tenant_id = tenant.id
    faculty_id = PydanticObjectId()
    session_date = date(2025, 9, 15)
    start = datetime.combine(session_date, time(10, 0), tzinfo=timezone.utc)
    end = datetime.combine(session_date, time(11, 0), tzinfo=timezone.utc)
    await ClassSession(
        tenant_id=tenant_id,
        faculty_user_id=faculty_id,
        course_code="CS101",
        section="A",
        session_type=SessionType.LECTURE,
        scheduled_start=start,
        scheduled_end=end,
        status="cancelled",
        academic_year_label="2025-26",
        semester_label="ODD",
    ).insert()
    expected, reason = await is_attendance_submission_expected(
        tenant_id,
        faculty_user_id=faculty_id,
        course_code="CS101",
        section="A",
        session_date=session_date,
    )
    assert expected is False
    assert reason == "class_session_cancelled"


@pytest.mark.anyio
async def test_cancelled_timetable_entry_excluded(db_ready) -> None:
    tenant = Tenant(name="T2", code=f"ae2_{uuid4().hex[:6]}", institution_email="t2@ex.com")
    await tenant.insert()
    tenant_id = tenant.id
    faculty_id = PydanticObjectId()
    session_date = date(2025, 9, 15)  # Monday
    await TimetableEntry(
        tenant_id=tenant_id,
        faculty_user_id=faculty_id,
        academic_year_label="2025-26",
        semester_label="ODD",
        day_of_week=session_date.weekday(),
        start_time=time(10, 0),
        end_time=time(11, 0),
        course_code="CS101",
        course_name="Prog",
        section="A",
        status=TimetableEntryStatus.CANCELLED,
    ).insert()
    expected, reason = await is_attendance_submission_expected(
        tenant_id,
        faculty_user_id=faculty_id,
        course_code="CS101",
        section="A",
        session_date=session_date,
    )
    assert expected is False
    assert reason == "timetable_slot_excluded"


@pytest.mark.anyio
async def test_filter_pending_drops_cancelled(db_ready) -> None:
    tenant = Tenant(name="T3", code=f"ae3_{uuid4().hex[:6]}", institution_email="t3@ex.com")
    await tenant.insert()
    tenant_id = tenant.id
    faculty_id = PydanticObjectId()
    session_date = date(2025, 9, 16)
    await TimetableEntry(
        tenant_id=tenant_id,
        faculty_user_id=faculty_id,
        academic_year_label="2025-26",
        semester_label="ODD",
        day_of_week=session_date.weekday(),
        start_time=time(9, 0),
        end_time=time(10, 0),
        course_code="CS102",
        course_name="Prog",
        section="B",
        status=TimetableEntryStatus.RESCHEDULED,
    ).insert()
    pending = PendingAttendanceSubmission(
        tenant_id=tenant_id,
        faculty_user_id=faculty_id,
        class_label="CS102",
        section="B",
        session_date=session_date,
        due_at=datetime.now(timezone.utc),
    )
    kept = await filter_pending_requiring_submission(tenant_id, [pending])
    assert len(kept) == 0