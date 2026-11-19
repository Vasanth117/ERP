"""Validation helpers for library facility configuration."""

from datetime import date

from app.core.exceptions import AppError
from app.modules.library.facility_enums import LibraryLocationLevel
from app.modules.library.facility_models import DayOperatingHours, OperatingSession

_LOCATION_PARENT: dict[LibraryLocationLevel, LibraryLocationLevel | None] = {
    LibraryLocationLevel.FLOOR: None,
    LibraryLocationLevel.ROOM: LibraryLocationLevel.FLOOR,
    LibraryLocationLevel.RACK: LibraryLocationLevel.ROOM,
    LibraryLocationLevel.SHELF: LibraryLocationLevel.RACK,
}


def _parse_hhmm(value: str) -> int:
    hour, minute = value.split(":")
    return int(hour) * 60 + int(minute)


def validate_operating_days(days: list[DayOperatingHours]) -> None:
    seen: set[int] = set()
    for day in days:
        if day.weekday in seen:
            raise AppError(code="VALIDATION_ERROR", message=f"Duplicate weekday {day.weekday}", status_code=422)
        seen.add(day.weekday)
        if day.is_closed:
            if day.sessions:
                raise AppError(
                    code="VALIDATION_ERROR",
                    message=f"Weekday {day.weekday} is closed but has sessions",
                    status_code=422,
                )
            continue
        if not day.sessions:
            raise AppError(
                code="VALIDATION_ERROR",
                message=f"Weekday {day.weekday} must include sessions or be marked closed",
                status_code=422,
            )
        intervals: list[tuple[int, int]] = []
        for session in day.sessions:
            start = _parse_hhmm(session.opens_at)
            end = _parse_hhmm(session.closes_at)
            if start >= end:
                raise AppError(
                    code="VALIDATION_ERROR",
                    message=f"Session on weekday {day.weekday} must open before it closes",
                    status_code=422,
                )
            intervals.append((start, end))
        intervals.sort()
        for idx in range(1, len(intervals)):
            if intervals[idx][0] < intervals[idx - 1][1]:
                raise AppError(
                    code="VALIDATION_ERROR",
                    message=f"Overlapping sessions on weekday {day.weekday}",
                    status_code=422,
                )


def validate_holiday_range(start_date: date, end_date: date) -> None:
    if end_date < start_date:
        raise AppError(code="VALIDATION_ERROR", message="Holiday end_date must be on or after start_date", status_code=422)


def validate_location_parent(
    level: LibraryLocationLevel,
    parent_level: LibraryLocationLevel | None,
) -> None:
    expected = _LOCATION_PARENT[level]
    if expected is None and parent_level is not None:
        raise AppError(code="VALIDATION_ERROR", message="Floor locations cannot have a parent", status_code=422)
    if expected is not None and parent_level != expected:
        raise AppError(
            code="VALIDATION_ERROR",
            message=f"A {level.value} location must have parent level {expected.value}",
            status_code=422,
        )