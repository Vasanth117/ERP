"""Rich operational data for showcase dashboards (finance, attendance, exams, approvals)."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from random import Random

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.roles import Role
from app.common.time import utcnow
from app.core.security import hash_password
from app.modules.academics.models import (
    AcademicCalendarEvent,
    ExaminationSchedule,
    PendingAssignmentEvaluation,
    PendingAttendanceSubmission,
)
from app.modules.attendance.enums import AttendanceMarkStatus, AttendanceSessionStatus
from app.modules.attendance.models import AttendanceRecord, AttendanceSession
from app.modules.auth.models import User
from app.modules.demo.constants import (
    DEMO_ACADEMIC_YEAR,
    DEMO_EMAIL_DOMAIN,
    DEMO_PASSWORD,
    DEMO_SEMESTER,
    DEPARTMENTS,
)
from app.modules.demo.seed.context import DemoSeedContext
from app.modules.faculty.models import FacultyProfile
from app.modules.finance.finance_enums import FeeDemandStatus, PaymentTransactionStatus
from app.modules.finance.finance_models import PaymentTransaction, StudentFeeDemand
from app.modules.hr.enums import LeaveRequestStatus
from app.modules.hr.models import EmployeeProfileSnapshot, LeaveRequest

_RNG = Random(2026)
_DESIGNATIONS = (
    "Professor",
    "Associate Professor",
    "Assistant Professor",
    "Senior Lecturer",
    "Lecturer",
)
_STAFF_ROLES = (Role.HR_STAFF, Role.ACCOUNTS_STAFF, Role.FINANCE_STAFF, Role.EXAMINATION_CELL, Role.LIBRARIAN)
_CHUNK = 400


async def _chunked_insert(model, docs: list) -> None:
    for offset in range(0, len(docs), _CHUNK):
        batch = docs[offset : offset + _CHUNK]
        if batch:
            await model.insert_many(batch)


async def _ensure_faculty_profiles(ctx: DemoSeedContext) -> None:
    tenant_id = ctx.tenant.id
    existing = await FacultyProfile.find(Eq(FacultyProfile.tenant_id, tenant_id)).count()
    if existing >= len(ctx.faculty_users) * 0.95:
        return
    linked = set(
        await FacultyProfile.get_motor_collection().distinct(
            "user_id",
            {"tenant_id": tenant_id},
        )
    )
    dept_codes = [d[0] for d in DEPARTMENTS]
    docs: list[FacultyProfile] = []
    for i, user in enumerate(ctx.faculty_users):
        if user.id in linked:
            continue
        docs.append(
            FacultyProfile(
                tenant_id=tenant_id,
                user_id=user.id,
                employee_id=f"FAC-{i+1:05d}",
                faculty_code=f"FAC{i+1:04d}",
                designation=_DESIGNATIONS[i % len(_DESIGNATIONS)],
                department_id=user.department_id,
                specialization=f"{dept_codes[i % len(dept_codes)]} core subjects",
                office_location=f"Block-{dept_codes[i % len(dept_codes)]}-{_RNG.randint(101, 420)}",
            )
        )
    await _chunked_insert(FacultyProfile, docs)


async def _ensure_non_faculty_employees(ctx: DemoSeedContext, *, target: int) -> None:
    tenant_id = ctx.tenant.id
    existing_snaps = await EmployeeProfileSnapshot.find(Eq(EmployeeProfileSnapshot.tenant_id, tenant_id)).count()
    faculty_snaps_needed = len(ctx.faculty_users)
    if existing_snaps >= faculty_snaps_needed + target * 0.9:
        return

    password_hash = hash_password(DEMO_PASSWORD)
    snap_docs: list[EmployeeProfileSnapshot] = []
    dept_name = DEPARTMENTS[0][1]
    linked_emp = set(
        await EmployeeProfileSnapshot.get_motor_collection().distinct(
            "employee_user_id",
            {"tenant_id": tenant_id},
        )
    )

    for i, faculty in enumerate(ctx.faculty_users):
        if faculty.id in linked_emp:
            continue
        snap_docs.append(
            EmployeeProfileSnapshot(
                tenant_id=tenant_id,
                employee_user_id=faculty.id,
                employee_id=f"EMP-FAC-{i+1:05d}",
                designation=_DESIGNATIONS[i % len(_DESIGNATIONS)],
                department_name=dept_name,
                joining_date=date(2008 + (i % 12), 7, 1),
                employment_type="permanent",
            )
        )

    staff_users: list[User] = []
    for i in range(target):
        email = f"staff{i+1:05d}@{DEMO_EMAIL_DOMAIN}"
        user = await User.find_one(Eq(User.email, email), Eq(User.tenant_id, tenant_id))
        if user is None:
            role = _STAFF_ROLES[i % len(_STAFF_ROLES)]
            user = User(
                email=email,
                hashed_password=password_hash,
                full_name=f"Staff Member {i + 1}",
                role=role,
                tenant_id=tenant_id,
                is_active=True,
            )
            await user.insert()
        staff_users.append(user)
        if user.id in linked_emp:
            continue
        snap_docs.append(
            EmployeeProfileSnapshot(
                tenant_id=tenant_id,
                employee_user_id=user.id,
                employee_id=f"EMP-NT-{i+1:05d}",
                designation="Administrative Officer" if i % 3 else "Technical Officer",
                department_name="Administration" if i % 2 else "Central Services",
                joining_date=date(2012 + (i % 8), 1, 15),
                employment_type="permanent",
            )
        )

    await _chunked_insert(EmployeeProfileSnapshot, snap_docs)


async def _seed_finance(ctx: DemoSeedContext) -> None:
    tenant_id = ctx.tenant.id
    if await PaymentTransaction.find(Eq(PaymentTransaction.tenant_id, tenant_id)).count() > 50:
        return

    demands: list[StudentFeeDemand] = []
    payments: list[PaymentTransaction] = []
    today = date.today()
    annual_fee = 185_000.0

    for i, student in enumerate(ctx.student_users):
        paid_ratio = 0.55 + (i % 45) / 100.0
        paid_amount = round(annual_fee * paid_ratio, 2)
        outstanding = round(max(annual_fee - paid_amount, 0), 2)
        if outstanding <= 0:
            status = FeeDemandStatus.PAID
        elif paid_amount > 0:
            status = FeeDemandStatus.PARTIALLY_PAID
        elif i % 17 == 0:
            status = FeeDemandStatus.OVERDUE
        else:
            status = FeeDemandStatus.OPEN

        demand_id = f"DEM-{DEMO_ACADEMIC_YEAR}-{i+1:06d}"
        demands.append(
            StudentFeeDemand(
                tenant_id=tenant_id,
                student_user_id=student.id,
                demand_id=demand_id,
                academic_year_label=DEMO_ACADEMIC_YEAR,
                semester_label=DEMO_SEMESTER,
                description="Tuition and semester fees",
                amount=outstanding if status != FeeDemandStatus.PAID else 0.0,
                due_date=today + timedelta(days=30 - (i % 25)),
                status=status,
            )
        )
        if paid_amount > 0:
            month_offset = (i % 6)
            payments.append(
                PaymentTransaction(
                    tenant_id=tenant_id,
                    student_user_id=student.id,
                    transaction_id=f"TX-{i+1:07d}",
                    idempotency_key=f"demo-pay-{tenant_id}-{i+1:07d}",
                    demand_id=demand_id,
                    amount=paid_amount,
                    status=PaymentTransactionStatus.SUCCESS,
                    gateway_reference=f"GATE-{i+1:07d}",
                    payment_mode="online" if i % 4 else "offline",
                    webhook_verified=True,
                    created_at=utcnow() - timedelta(days=month_offset * 28 + (i % 20)),
                )
            )

    await _chunked_insert(StudentFeeDemand, demands)
    await _chunked_insert(PaymentTransaction, payments)


async def _seed_attendance_scale(ctx: DemoSeedContext) -> None:
    tenant_id = ctx.tenant.id
    submitted = await AttendanceSession.find(
        Eq(AttendanceSession.tenant_id, tenant_id),
        Eq(AttendanceSession.status, AttendanceSessionStatus.SUBMITTED),
    ).count()
    if submitted >= 200:
        return
    if not ctx.faculty_users or not ctx.student_users:
        return

    dept_codes = [d[0] for d in DEPARTMENTS]
    sessions: list[AttendanceSession] = []
    today = date.today()
    session_index = 0

    for week in range(14):
        for weekday in range(5):
            for slot in range(3):
                day_offset = week * 7 + weekday
                session_date = today - timedelta(days=day_offset + 7)
                faculty = ctx.faculty_users[(week + weekday + slot) % len(ctx.faculty_users)]
                dept_code = dept_codes[(week + slot) % len(dept_codes)]
                sessions.append(
                    AttendanceSession(
                        tenant_id=tenant_id,
                        faculty_user_id=faculty.id,
                        course_id=f"{dept_code.lower()}{100 + slot}",
                        course_code=f"{dept_code}{100 + slot}",
                        section="A" if slot % 2 == 0 else "B",
                        session_date=session_date,
                        academic_year_label=DEMO_ACADEMIC_YEAR,
                        semester_label=DEMO_SEMESTER,
                        status=AttendanceSessionStatus.SUBMITTED,
                        submitted_at=utcnow() - timedelta(days=day_offset),
                    )
                )
                session_index += 1

    await _chunked_insert(AttendanceSession, sessions)

    records: list[AttendanceRecord] = []
    for idx, session in enumerate(sessions):
        if session.id is None:
            continue
        cohort_start = (idx * 41) % max(len(ctx.student_users) - 50, 1)
        cohort = ctx.student_users[cohort_start : cohort_start + 48]
        for si, student in enumerate(cohort):
            status = AttendanceMarkStatus.PRESENT
            if si % 9 == 0:
                status = AttendanceMarkStatus.ABSENT
            elif si % 14 == 0:
                status = AttendanceMarkStatus.LATE
            records.append(
                AttendanceRecord(
                    tenant_id=tenant_id,
                    session_id=session.id,
                    student_user_id=student.id,
                    status=status,
                )
            )

    pending_docs: list[PendingAttendanceSubmission] = []
    for i in range(12):
        faculty = ctx.faculty_users[i % len(ctx.faculty_users)]
        dept = dept_codes[i % len(dept_codes)]
        pending_docs.append(
            PendingAttendanceSubmission(
                tenant_id=tenant_id,
                faculty_user_id=faculty.id,
                class_label=f"{dept} Lecture",
                section="A" if i % 2 == 0 else "B",
                session_date=today - timedelta(days=i),
                due_at=utcnow() + timedelta(days=1 + i),
                course_code=f"{dept}10{i % 3}",
            )
        )

    await _chunked_insert(AttendanceRecord, records)
    await _chunked_insert(PendingAttendanceSubmission, pending_docs)


async def _seed_exams_and_calendar(ctx: DemoSeedContext) -> None:
    tenant_id = ctx.tenant.id
    if await ExaminationSchedule.find(Eq(ExaminationSchedule.tenant_id, tenant_id)).count() >= 40:
        await _seed_calendar_only(tenant_id)
        return

    now = utcnow()
    dept_codes = [d[0] for d in DEPARTMENTS]
    exams: list[ExaminationSchedule] = []
    for i in range(120):
        dept = dept_codes[i % len(dept_codes)]
        faculty = ctx.faculty_users[i % len(ctx.faculty_users)] if ctx.faculty_users else None
        start = now + timedelta(days=3 + (i % 40), hours=(i % 5) * 2)
        exams.append(
            ExaminationSchedule(
                tenant_id=tenant_id,
                faculty_user_id=faculty.id if faculty else None,
                course_code=f"{dept}{200 + (i % 8)}",
                section="A" if i % 2 == 0 else "B",
                exam_type="semester" if i % 4 == 0 else "internal",
                title=f"{dept} {DEMO_SEMESTER} assessment",
                scheduled_at=start,
                scheduled_end=start + timedelta(hours=3),
                room=f"Exam Hall {_RNG.randint(1, 12)}",
                academic_year_label=DEMO_ACADEMIC_YEAR,
                semester_label=DEMO_SEMESTER,
            )
        )

    evals: list[PendingAssignmentEvaluation] = []
    for i in range(25):
        faculty = ctx.faculty_users[i % len(ctx.faculty_users)]
        dept = dept_codes[i % len(dept_codes)]
        evals.append(
            PendingAssignmentEvaluation(
                tenant_id=tenant_id,
                faculty_user_id=faculty.id,
                assignment_id=f"ASG-{i+1:04d}",
                title=f"{dept} internals batch {i+1}",
                course_code=f"{dept}301",
                submissions_pending=12 + (i % 30),
                due_at=now + timedelta(days=2 + i),
            )
        )

    leaves: list[LeaveRequest] = []
    for i in range(18):
        emp = ctx.faculty_users[(i * 3) % len(ctx.faculty_users)]
        start = date.today() + timedelta(days=3 + i)
        leaves.append(
            LeaveRequest(
                tenant_id=tenant_id,
                employee_user_id=emp.id,
                leave_type="casual" if i % 2 == 0 else "medical",
                start_date=start,
                end_date=start + timedelta(days=1 + (i % 3)),
                reason="Demo pending approval item",
                status=LeaveRequestStatus.SUBMITTED,
            )
        )

    await _chunked_insert(ExaminationSchedule, exams)
    await _chunked_insert(PendingAssignmentEvaluation, evals)
    await _chunked_insert(LeaveRequest, leaves)
    await _seed_calendar_only(tenant_id)


async def _seed_calendar_only(tenant_id: PydanticObjectId) -> None:
    if await AcademicCalendarEvent.find(Eq(AcademicCalendarEvent.tenant_id, tenant_id)).count() >= 8:
        return
    now = datetime.now(timezone.utc)
    titles = (
        "Mid-semester examinations",
        "Industry expert lecture — AI in manufacturing",
        "Sports day",
        "Dept. Heads council",
        "Alumni meet",
        "Internal assessment week",
        "Convocation rehearsal",
        "National symposium keynote",
    )
    events = [
        AcademicCalendarEvent(
            tenant_id=tenant_id,
            title=title,
            description="Showcase calendar event for demo dashboards.",
            event_at=now + timedelta(days=2 + i * 3),
            event_type="academic" if i % 2 == 0 else "general",
            audience="all",
        )
        for i, title in enumerate(titles)
    ]
    await _chunked_insert(AcademicCalendarEvent, events)


async def seed_showcase_analytics(ctx: DemoSeedContext, *, non_faculty_employees: int) -> None:
    """Populate dashboard readers with enterprise-scale sample data."""
    await _ensure_faculty_profiles(ctx)
    await _ensure_non_faculty_employees(ctx, target=non_faculty_employees)
    await _seed_finance(ctx)
    await _seed_attendance_scale(ctx)
    await _seed_exams_and_calendar(ctx)