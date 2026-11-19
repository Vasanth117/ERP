"""Working-day leave duration with institutional calendar hints."""

from datetime import date, datetime, time, timedelta

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, GTE, LTE

from app.modules.academics.models import AcademicCalendarEvent
from app.modules.hr.enums import LeaveDayPortion


async def tenant_holiday_dates(tenant_id: PydanticObjectId, start: date, end: date) -> set[date]:
    """Dates marked as holidays on the academic calendar (event_type=holiday)."""
    start_dt = datetime.combine(start, time.min)
    end_dt = datetime.combine(end, time.max)
    events = await AcademicCalendarEvent.find(
        Eq(AcademicCalendarEvent.tenant_id, tenant_id),
        GTE(AcademicCalendarEvent.event_at, start_dt),
        LTE(AcademicCalendarEvent.event_at, end_dt),
    ).to_list()
    holidays: set[date] = set()
    for event in events:
        if event.event_type not in {"holiday", "institution_holiday", "closure"}:
            continue
        holidays.add(event.event_at.date())
    return holidays


async def count_working_leave_days(
    tenant_id: PydanticObjectId,
    start: date,
    end: date,
    day_portion: LeaveDayPortion,
) -> float:
    if end < start:
        return 0.0
    holidays = await tenant_holiday_dates(tenant_id, start, end)
    days = 0.0
    d = start
    while d <= end:
        if d.weekday() < 5 and d not in holidays:
            days += 1.0
        d += timedelta(days=1)
    if days == 0:
        return 0.5 if day_portion != LeaveDayPortion.FULL else 1.0
    if day_portion != LeaveDayPortion.FULL and start == end:
        return 0.5
    return days