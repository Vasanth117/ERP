"""Derive attendance status and durations from events and schedules."""

from datetime import date, datetime, time, timedelta
from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.modules.academics.models import AcademicCalendarEvent
from app.modules.hr.attendance_schedule_models import HrEmployeeAttendanceEvent, HrEmployeeRosterAssignment, HrShift, HrWorkSchedule
from app.modules.hr.enums import EmployeeAttendanceDayStatus, HrAttendanceEventType
from app.modules.hr.leave_working_days import tenant_holiday_dates
from app.modules.hr.models import LeaveRequest
from app.modules.hr.enums import LeaveRequestStatus


def _parse_time(value: str) -> time:
    hour, minute = value.split(":")[:2]
    return time(int(hour), int(minute))


def _combine(attendance_date: date, t: time) -> datetime:
    return datetime.combine(attendance_date, t)


def _naive(dt: datetime) -> datetime:
    return dt.replace(tzinfo=None) if dt.tzinfo else dt


async def resolve_schedule_and_shift(
    tenant_id: PydanticObjectId,
    employee_user_id: PydanticObjectId,
    attendance_date: date,
) -> tuple[HrWorkSchedule | None, HrShift | None]:
    roster = await HrEmployeeRosterAssignment.find_one(
        Eq(HrEmployeeRosterAssignment.tenant_id, tenant_id),
        Eq(HrEmployeeRosterAssignment.employee_user_id, employee_user_id),
        Eq(HrEmployeeRosterAssignment.roster_date, attendance_date),
    )
    shift = None
    schedule = None
    if roster:
        shift = await HrShift.get(roster.shift_id)
        if roster.schedule_id:
            schedule = await HrWorkSchedule.get(roster.schedule_id)
    if schedule is None:
        rows = await HrWorkSchedule.find(
            Eq(HrWorkSchedule.tenant_id, tenant_id),
            Eq(HrWorkSchedule.is_active, True),
        ).sort(-HrWorkSchedule.version).limit(1).to_list()
        schedule = rows[0] if rows else None
    return schedule, shift


async def is_on_approved_leave(tenant_id: PydanticObjectId, employee_user_id: PydanticObjectId, attendance_date: date) -> bool:
    leaves = await LeaveRequest.find(
        Eq(LeaveRequest.tenant_id, tenant_id),
        Eq(LeaveRequest.employee_user_id, employee_user_id),
        Eq(LeaveRequest.status, LeaveRequestStatus.APPROVED),
    ).to_list()
    for leave in leaves:
        if leave.start_date <= attendance_date <= leave.end_date:
            return True
    return False


async def compute_attendance_from_events(
    tenant_id: PydanticObjectId,
    employee_user_id: PydanticObjectId,
    attendance_date: date,
    events: list[HrEmployeeAttendanceEvent],
) -> dict:
    schedule, shift = await resolve_schedule_and_shift(tenant_id, employee_user_id, attendance_date)
    holidays = await tenant_holiday_dates(tenant_id, attendance_date, attendance_date)
    if attendance_date in holidays:
        return {
            "status": EmployeeAttendanceDayStatus.HOLIDAY,
            "working_minutes": 0,
            "break_minutes": 0,
            "late_minutes": 0,
            "early_departure_minutes": 0,
            "overtime_minutes": 0,
            "missing_punch": False,
            "first_check_in": None,
            "last_check_out": None,
            "shift_id": shift.id if shift else None,
            "schedule_id": schedule.id if schedule else None,
        }

    if schedule and attendance_date.weekday() in schedule.weekly_offs:
        return {
            "status": EmployeeAttendanceDayStatus.WEEKLY_OFF,
            "working_minutes": 0,
            "break_minutes": 0,
            "late_minutes": 0,
            "early_departure_minutes": 0,
            "overtime_minutes": 0,
            "missing_punch": False,
            "first_check_in": None,
            "last_check_out": None,
            "shift_id": shift.id if shift else None,
            "schedule_id": schedule.id if schedule else None,
        }

    if await is_on_approved_leave(tenant_id, employee_user_id, attendance_date):
        return {
            "status": EmployeeAttendanceDayStatus.ON_LEAVE,
            "working_minutes": 0,
            "break_minutes": 0,
            "late_minutes": 0,
            "early_departure_minutes": 0,
            "overtime_minutes": 0,
            "missing_punch": False,
            "first_check_in": None,
            "last_check_out": None,
            "shift_id": shift.id if shift else None,
            "schedule_id": schedule.id if schedule else None,
        }

    check_ins = sorted([e for e in events if e.event_type == HrAttendanceEventType.CHECK_IN], key=lambda e: e.event_at)
    check_outs = sorted([e for e in events if e.event_type == HrAttendanceEventType.CHECK_OUT], key=lambda e: e.event_at)

    if not check_ins and not check_outs:
        if schedule and attendance_date.weekday() in schedule.working_days:
            return {
                "status": EmployeeAttendanceDayStatus.ABSENT,
                "working_minutes": 0,
                "break_minutes": schedule.break_minutes if schedule else 0,
                "late_minutes": 0,
                "early_departure_minutes": 0,
                "overtime_minutes": 0,
                "missing_punch": True,
                "first_check_in": None,
                "last_check_out": None,
                "shift_id": shift.id if shift else None,
                "schedule_id": schedule.id if schedule else None,
            }
        return {
            "status": EmployeeAttendanceDayStatus.ABSENT,
            "working_minutes": 0,
            "break_minutes": 0,
            "late_minutes": 0,
            "early_departure_minutes": 0,
            "overtime_minutes": 0,
            "missing_punch": False,
            "first_check_in": None,
            "last_check_out": None,
            "shift_id": shift.id if shift else None,
            "schedule_id": schedule.id if schedule else None,
        }

    first_in = check_ins[0].event_at if check_ins else None
    last_out = check_outs[-1].event_at if check_outs else None
    missing_punch = first_in is None or last_out is None
    status = EmployeeAttendanceDayStatus.INCOMPLETE if missing_punch else EmployeeAttendanceDayStatus.PRESENT

    ref_start = _parse_time(shift.start_time) if shift else (_parse_time(schedule.start_time) if schedule else time(9, 0))
    ref_end = _parse_time(shift.end_time) if shift else (_parse_time(schedule.end_time) if schedule else time(18, 0))
    grace = shift.grace_minutes if shift else (schedule.grace_minutes if schedule else 15)
    break_mins = shift.break_minutes if shift else (schedule.break_minutes if schedule else 60)
    expected_mins = int((shift.expected_hours if shift else (schedule.expected_hours if schedule else 8)) * 60)

    late_minutes = 0
    early_minutes = 0
    if first_in and schedule:
        scheduled_start = _combine(attendance_date, ref_start)
        if shift and shift.crosses_midnight:
            scheduled_start = _combine(attendance_date, ref_start)
        first_cmp = _naive(first_in)
        if first_cmp > scheduled_start + timedelta(minutes=grace):
            late_minutes = int((first_cmp - scheduled_start).total_seconds() // 60) - grace
            status = EmployeeAttendanceDayStatus.LATE if not missing_punch else EmployeeAttendanceDayStatus.MISSING_PUNCH

    if last_out and schedule:
        scheduled_end = _combine(attendance_date, ref_end)
        if shift and shift.crosses_midnight:
            scheduled_end = _combine(attendance_date + timedelta(days=1), ref_end)
        last_cmp = _naive(last_out)
        if last_cmp < scheduled_end - timedelta(minutes=grace):
            early_minutes = int((scheduled_end - last_cmp).total_seconds() // 60) - grace
            if status == EmployeeAttendanceDayStatus.PRESENT:
                status = EmployeeAttendanceDayStatus.EARLY_DEPARTURE

    working_minutes = 0
    if first_in and last_out and _naive(last_out) > _naive(first_in):
        working_minutes = max(0, int((_naive(last_out) - _naive(first_in)).total_seconds() // 60) - break_mins)

    overtime_minutes = max(0, working_minutes - expected_mins)
    if working_minutes > 0 and working_minutes < expected_mins // 2 and not missing_punch:
        status = EmployeeAttendanceDayStatus.HALF_DAY

    return {
        "status": status,
        "working_minutes": working_minutes,
        "break_minutes": break_mins,
        "late_minutes": max(0, late_minutes),
        "early_departure_minutes": max(0, early_minutes),
        "overtime_minutes": overtime_minutes,
        "missing_punch": missing_punch,
        "first_check_in": first_in,
        "last_check_out": last_out,
        "shift_id": shift.id if shift else None,
        "schedule_id": schedule.id if schedule else None,
    }