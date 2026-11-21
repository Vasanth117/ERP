"""Academic calendar configuration page (CA — college admin academics)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.college_admin.academic_config_models import (
    AcademicCalendar,
    AcademicCalendarEventEmbed,
    AcademicTerm,
    AcademicYear,
    ConfigPublicationStatus,
)
from app.modules.college_admin.academic_config_service import publish_calendar
from app.modules.college_admin.institution_calendar_models import InstitutionHoliday
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AcademicCalendarAddEventForm,
    AcademicCalendarAddEventSave,
    AcademicCalendarConfigurationPageRead,
    AcademicCalendarEventTableRow,
    AcademicCalendarPublishSave,
    AcademicCalendarTypeStatRow,
    AcademicCalendarViewTab,
    InstitutionFieldMeta,
    InstitutionFieldOption,
    PoliciesPagination,
)
from app.modules.college_admin.years_semesters_nav import years_semesters_sub_nav

_PAGE_SIZE = 8
_CALENDAR_TITLE = "Academic events calendar"

_EVENT_TYPE_OPTIONS: list[InstitutionFieldOption] = [
    InstitutionFieldOption(value="examination", label="Examination"),
    InstitutionFieldOption(value="meeting", label="Meeting"),
    InstitutionFieldOption(value="deadline", label="Deadline"),
    InstitutionFieldOption(value="academic", label="Academic"),
    InstitutionFieldOption(value="holiday", label="Holiday"),
    InstitutionFieldOption(value="registration", label="Registration"),
    InstitutionFieldOption(value="general", label="General"),
]

_TYPE_LABELS: dict[str, str] = {opt.value: opt.label for opt in _EVENT_TYPE_OPTIONS}

_AUDIENCE_OPTIONS: list[InstitutionFieldOption] = [
    InstitutionFieldOption(value="all", label="All students"),
    InstitutionFieldOption(value="students", label="Students"),
    InstitutionFieldOption(value="faculty", label="Faculty"),
    InstitutionFieldOption(value="parents", label="Parents"),
    InstitutionFieldOption(value="staff", label="Staff"),
]

_AUDIENCE_LABELS: dict[str, str] = {
    "all": "All",
    "students": "Students",
    "faculty": "Faculty",
    "parents": "Parents",
    "staff": "Staff",
}

_STATUS_PRESENTATION: dict[str, tuple[str, str]] = {
    "published": ("Published", "success"),
    "draft": ("Draft", "warning"),
}

_MONTH_NAMES = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


@dataclass
class _CollectedEvent:
    event_id: str
    title: str
    start: date
    end: date | None
    type_code: str
    audience_code: str
    status_code: str
    sort_at: datetime
    calendar_id: str | None


def _format_day(d: date) -> str:
    return f"{d.day:02d} {_MONTH_NAMES[d.month - 1][:3]}"


def _format_date_range(start: date, end: date | None) -> str:
    if end and end != start:
        if start.month == end.month and start.year == end.year:
            return f"{start.day:02d} – {end.day:02d} {_MONTH_NAMES[start.month - 1][:3]}"
        return f"{_format_day(start)} – {_format_day(end)}"
    return _format_day(start)


def _date_to_dt(d: date) -> datetime:
    return datetime.combine(d, time(9, 0))


def _event_end_date(event_at: datetime, event_end_at: datetime | None) -> date | None:
    if event_end_at is None:
        return None
    end = event_end_at.date()
    if end == event_at.date():
        return None
    return end


def _type_label(code: str) -> str:
    lowered = code.lower().strip()
    for key, label in _TYPE_LABELS.items():
        if key in lowered or lowered == key:
            return label
    if "exam" in lowered:
        return "Examination"
    if "holiday" in lowered:
        return "Holiday"
    if "meet" in lowered:
        return "Meeting"
    return code.replace("_", " ").title() if code else "General"


def _audience_label(code: str, *, term_label: str | None = None) -> str:
    if term_label:
        return term_label
    return _AUDIENCE_LABELS.get(code.lower(), code.replace("_", " ").title())


def _status_for_embed(status: str, *, calendar_status: ConfigPublicationStatus) -> str:
    if status and status.lower() == "published":
        return "published"
    if calendar_status == ConfigPublicationStatus.PUBLISHED and status.lower() != "draft":
        return "published"
    return "draft"


def _holiday_type_code(holiday_type: str) -> str:
    lowered = holiday_type.lower()
    if "gazetted" in lowered or "national" in lowered:
        return "holiday"
    return "holiday"


def _page_numbers(total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if total_pages <= 12:
        return list(range(1, total_pages + 1))
    return [1, 2, 3, -1, total_pages]


def _window_for_view(
    view: str,
    *,
    today: date,
    year: AcademicYear,
    month_key: str | None,
    term: AcademicTerm | None,
) -> tuple[date, date, str]:
    if view == "semester" and term and term.start_date and term.end_date:
        title = f"Semester events – {term.label}"
        return term.start_date, term.end_date, title
    if view == "month":
        if month_key and len(month_key) >= 7:
            try:
                year_part, month_part = month_key.split("-", 1)
                y, m = int(year_part), int(month_part)
                start = date(y, m, 1)
                if m == 12:
                    end = date(y + 1, 1, 1) - timedelta(days=1)
                else:
                    end = date(y, m + 1, 1) - timedelta(days=1)
                return start, end, f"Events – {_MONTH_NAMES[m - 1]} {y}"
            except ValueError:
                pass
        start = today.replace(day=1)
        if start.month == 12:
            end = date(start.year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(start.year, start.month + 1, 1) - timedelta(days=1)
        return start, end, f"Events – {_MONTH_NAMES[start.month - 1]} {start.year}"

    start = today
    end_month = today.month + 1
    end_year = today.year
    if end_month > 12:
        end_month = 1
        end_year += 1
    end = date(end_year, end_month, 1)
    if end.month == 12:
        range_end = date(end.year + 1, 1, 1) - timedelta(days=1)
    else:
        range_end = date(end.year, end.month + 1, 1) - timedelta(days=1)
    range_start = today
    if year.start_date and range_start < year.start_date:
        range_start = year.start_date
    if year.end_date and range_end > year.end_date:
        range_end = year.end_date
    m1 = _MONTH_NAMES[range_start.month - 1]
    m2 = _MONTH_NAMES[range_end.month - 1]
    if range_start.month == range_end.month:
        panel = f"Upcoming events – {m1} {range_start.year}"
    else:
        panel = f"Upcoming events – {m1} & {m2} {range_end.year}"
    return range_start, range_end, panel


def _event_in_range(ev: _CollectedEvent, start: date, end: date) -> bool:
    ev_end = ev.end or ev.start
    return ev.start <= end and ev_end >= start


async def _resolve_year(
    tenant_id: PydanticObjectId,
    academic_year_id: str | None,
) -> AcademicYear | None:
    years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-start_date").to_list()
    if not years:
        return None
    if academic_year_id:
        try:
            picked = await AcademicYear.get(PydanticObjectId(academic_year_id))
            if picked and picked.tenant_id == tenant_id:
                return picked
        except Exception:
            pass
    return next((y for y in years if y.is_current), years[0])


async def _primary_calendar(tenant_id: PydanticObjectId, year_id: PydanticObjectId) -> AcademicCalendar:
    calendars = await AcademicCalendar.find(
        Eq(AcademicCalendar.tenant_id, tenant_id),
        Eq(AcademicCalendar.academic_year_id, year_id),
    ).to_list()
    for cal in calendars:
        if cal.title.strip().lower() == _CALENDAR_TITLE.lower():
            return cal
    if calendars:
        return max(calendars, key=lambda c: len(c.events))
    doc = AcademicCalendar(
        tenant_id=tenant_id,
        academic_year_id=year_id,
        title=_CALENDAR_TITLE,
        events=[],
        status=ConfigPublicationStatus.DRAFT,
    )
    await doc.insert()
    return doc


async def _collect_events(
    tenant_id: PydanticObjectId,
    year: AcademicYear,
    calendars: list[AcademicCalendar],
    terms: list[AcademicTerm],
    holidays: list[InstitutionHoliday],
) -> list[_CollectedEvent]:
    collected: list[_CollectedEvent] = []
    seen_titles: set[tuple[str, date]] = set()

    for calendar in calendars:
        for event in calendar.events:
            start = event.event_at.date()
            end = _event_end_date(event.event_at, event.event_end_at)
            status = _status_for_embed(event.status, calendar_status=calendar.status)
            key = (event.title.strip().lower(), start)
            seen_titles.add(key)
            collected.append(
                _CollectedEvent(
                    event_id=event.event_id,
                    title=event.title,
                    start=start,
                    end=end,
                    type_code=event.event_type,
                    audience_code=event.audience,
                    status_code=status,
                    sort_at=event.event_at,
                    calendar_id=str(calendar.id),
                )
            )

    term_milestones: list[tuple[str, str, date | None, str, str]] = [
        ("mid_semester_exam_date", "Mid-semester examinations", None, "examination", "students"),
        ("end_semester_exam_date", "End-semester examinations", None, "examination", "students"),
        ("last_instruction_day", "Last instruction day", None, "deadline", "students"),
        ("course_registration_opens", "Course registration opens", None, "registration", "students"),
        ("add_drop_deadline", "Add/drop deadline", None, "deadline", "students"),
    ]
    for term in terms:
        audience = term.label
        for field, title, _, type_code, aud in term_milestones:
            raw = getattr(term, field, None)
            if raw is None:
                continue
            key = (title.lower(), raw)
            if key in seen_titles:
                continue
            term_status = "published" if term.status == ConfigPublicationStatus.PUBLISHED else "draft"
            collected.append(
                _CollectedEvent(
                    event_id=f"term-{term.id}-{field}",
                    title=title if "examinations" not in title else f"{title} ({term.label})",
                    start=raw,
                    end=None,
                    type_code=type_code,
                    audience_code=aud,
                    status_code=term_status,
                    sort_at=_date_to_dt(raw),
                    calendar_id=None,
                )
            )

    for holiday in holidays:
        end = holiday.end_date
        collected.append(
            _CollectedEvent(
                event_id=f"holiday-{holiday.holiday_id}",
                title=holiday.title,
                start=holiday.start_date,
                end=end if end and end != holiday.start_date else None,
                type_code=_holiday_type_code(holiday.holiday_type),
                audience_code=holiday.applies_to,
                status_code="published",
                sort_at=_date_to_dt(holiday.start_date),
                calendar_id=None,
            )
        )

    collected.sort(key=lambda row: (row.start, row.title.lower()))
    return collected


async def get_academic_calendar_configuration_page(
    scope: AccessScope,
    *,
    view: str = "list",
    page: int = 1,
    academic_year_id: str | None = None,
    month: str | None = None,
    term_id: str | None = None,
) -> AcademicCalendarConfigurationPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_READ)
    tenant_id = require_college_tenant_scope(scope)
    today = utcnow().date()
    generated = utcnow()
    view_key = view if view in {"list", "month", "semester"} else "list"

    year = await _resolve_year(tenant_id, academic_year_id)
    if year is None:
        snapshot = generated.astimezone().strftime("%d %b %Y, %H:%M IST")
        return AcademicCalendarConfigurationPageRead(
            page_title="Academic Calendar Configuration",
            page_subtitle="Events, deadlines and examination windows",
            publish_button_label="Publish calendar",
            add_event_button_label="Add event",
            can_publish=False,
            primary_calendar_id=None,
            active_view=view_key,
            view_tabs=[
                AcademicCalendarViewTab(key="list", label="List", active=view_key == "list"),
                AcademicCalendarViewTab(key="month", label="Month", active=view_key == "month"),
                AcademicCalendarViewTab(key="semester", label="Semester view", active=view_key == "semester"),
            ],
            list_panel_title="Upcoming events",
            table_headers=["Event", "Date", "Type", "Audience", "Status"],
            event_rows=[],
            year_event_count_label="0 events this year",
            pagination=PoliciesPagination(
                page=1,
                page_size=_PAGE_SIZE,
                total=0,
                total_pages=0,
                page_numbers=[],
                has_previous=False,
                has_next=False,
            ),
            add_event_form=_empty_add_form(),
            type_stats_title="Events by type",
            type_stats=[],
            selected_academic_year_id="",
            sub_nav=years_semesters_sub_nav(active="calendar"),
            footer_disclaimer="Illustrative data only · No live student, faculty or finance records · All times IST",
            footer_snapshot_label=f"Sample snapshot · {snapshot}",
            generated_at=generated,
        )

    terms = await AcademicTerm.find(
        Eq(AcademicTerm.tenant_id, tenant_id),
        Eq(AcademicTerm.academic_year_id, year.id),
    ).to_list()
    selected_term: AcademicTerm | None = None
    if term_id:
        try:
            picked = next((t for t in terms if str(t.id) == term_id), None)
            selected_term = picked
        except Exception:
            selected_term = None
    if selected_term is None:
        selected_term = next((t for t in terms if t.is_current), terms[0] if terms else None)

    calendars = await AcademicCalendar.find(
        Eq(AcademicCalendar.tenant_id, tenant_id),
        Eq(AcademicCalendar.academic_year_id, year.id),
    ).to_list()
    holidays = await InstitutionHoliday.find(
        Eq(InstitutionHoliday.tenant_id, tenant_id),
        Eq(InstitutionHoliday.academic_year_id, year.id),
    ).to_list()

    all_events = await _collect_events(tenant_id, year, calendars, terms, holidays)
    year_total = len(all_events)

    window_start, window_end, panel_title = _window_for_view(
        view_key,
        today=today,
        year=year,
        month_key=month,
        term=selected_term,
    )
    filtered = [ev for ev in all_events if _event_in_range(ev, window_start, window_end)]
    if not filtered and view_key == "list":
        filtered = [ev for ev in all_events if ev.start >= today]
    if not filtered:
        filtered = all_events

    total = len(filtered)
    total_pages = max(1, math.ceil(total / _PAGE_SIZE)) if total else 0
    page = min(max(1, page), total_pages or 1)
    offset = (page - 1) * _PAGE_SIZE
    page_slice = filtered[offset : offset + _PAGE_SIZE]

    event_rows = [
        AcademicCalendarEventTableRow(
            event_id=row.event_id,
            title=row.title,
            date_label=_format_date_range(row.start, row.end),
            type_label=_type_label(row.type_code),
            audience_label=_audience_label(row.audience_code),
            status_label=_STATUS_PRESENTATION.get(row.status_code, ("Draft", "warning"))[0],
            status_tone=_STATUS_PRESENTATION.get(row.status_code, ("Draft", "warning"))[1],
        )
        for row in page_slice
    ]

    type_counts: dict[str, int] = {}
    for ev in all_events:
        label = _type_label(ev.type_code)
        type_counts[label] = type_counts.get(label, 0) + 1
    max_count = max(type_counts.values(), default=1)
    type_stats = [
        AcademicCalendarTypeStatRow(
            type_label=label,
            count=count,
            bar_percent=round(100 * count / max_count, 1),
        )
        for label, count in sorted(type_counts.items(), key=lambda pair: (-pair[1], pair[0]))
    ]

    primary = await _primary_calendar(tenant_id, year.id)
    can_publish = primary.status == ConfigPublicationStatus.DRAFT and len(primary.events) > 0

    snapshot = generated.astimezone().strftime("%d %b %Y, %H:%M IST")
    subtitle = f"Events, deadlines and examination windows for {year.label}"

    return AcademicCalendarConfigurationPageRead(
        page_title="Academic Calendar Configuration",
        page_subtitle=subtitle,
        publish_button_label="Publish calendar",
        add_event_button_label="Add event",
        can_publish=can_publish,
        primary_calendar_id=str(primary.id),
        active_view=view_key,
        view_tabs=[
            AcademicCalendarViewTab(key="list", label="List", active=view_key == "list"),
            AcademicCalendarViewTab(key="month", label="Month", active=view_key == "month"),
            AcademicCalendarViewTab(key="semester", label="Semester view", active=view_key == "semester"),
        ],
        list_panel_title=panel_title,
        table_headers=["Event", "Date", "Type", "Audience", "Status"],
        event_rows=event_rows,
        year_event_count_label=f"{year_total} event{'s' if year_total != 1 else ''} this year",
        pagination=PoliciesPagination(
            page=page,
            page_size=_PAGE_SIZE,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        add_event_form=_default_add_form(),
        type_stats_title="Events by type",
        type_stats=type_stats,
        selected_academic_year_id=str(year.id),
        selected_term_id=str(selected_term.id) if selected_term else None,
        sub_nav=years_semesters_sub_nav(active="calendar"),
        footer_disclaimer="Illustrative data only · No live student, faculty or finance records · All times IST",
        footer_snapshot_label=f"Sample snapshot · {snapshot}",
        generated_at=generated,
    )


def _empty_add_form() -> AcademicCalendarAddEventForm:
    return _default_add_form()


def _default_add_form() -> AcademicCalendarAddEventForm:
    return AcademicCalendarAddEventForm(
        title_meta=InstitutionFieldMeta(key="title", label="Event title", required=True),
        title_placeholder="e.g. Annual sports day",
        type_meta=InstitutionFieldMeta(key="event_type", label="Type", required=True, field_type="select"),
        type_options=_EVENT_TYPE_OPTIONS,
        type_default_value="academic",
        from_meta=InstitutionFieldMeta(key="from_date", label="From", required=True, field_type="date"),
        to_meta=InstitutionFieldMeta(key="to_date", label="To", required=False, field_type="date"),
        audience_meta=InstitutionFieldMeta(key="audience", label="Audience", required=True, field_type="select"),
        audience_options=_AUDIENCE_OPTIONS,
        audience_default_value="all",
        submit_label="Save event",
    )


async def add_academic_calendar_event(
    scope: AccessScope,
    payload: AcademicCalendarAddEventSave,
) -> AcademicCalendarConfigurationPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    year_id = PydanticObjectId(payload.academic_year_id)
    year = await AcademicYear.get(year_id)
    if year is None or year.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Academic year not found", status_code=404)
    if payload.to_date and payload.to_date < payload.from_date:
        raise AppError(code="VALIDATION_ERROR", message="End date must be on or after start date", status_code=422)

    calendar = await _primary_calendar(tenant_id, year_id)
    event_at = _date_to_dt(payload.from_date)
    event_end = _date_to_dt(payload.to_date) if payload.to_date else None
    embed = AcademicCalendarEventEmbed(
        title=payload.title.strip(),
        event_at=event_at,
        event_end_at=event_end,
        event_type=payload.event_type,
        audience=payload.audience,
        status="draft",
    )
    calendar.events.append(embed)
    calendar.updated_at = utcnow()
    await calendar.save()
    await record_audit(
        tenant_id=tenant_id,
        actor_id=scope.user_id,
        action="academic_calendar.event_added",
        resource_type="academic_calendar",
        resource_id=str(calendar.id),
        metadata={"event_id": embed.event_id, "title": embed.title},
    )
    return await get_academic_calendar_configuration_page(
        scope,
        academic_year_id=str(year.id),
    )


async def publish_academic_calendar_configuration(
    scope: AccessScope,
    payload: AcademicCalendarPublishSave,
) -> AcademicCalendarConfigurationPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    year_id = PydanticObjectId(payload.academic_year_id)
    year = await AcademicYear.get(year_id)
    if year is None or year.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Academic year not found", status_code=404)

    if payload.calendar_id:
        calendar_id = PydanticObjectId(payload.calendar_id)
    else:
        primary = await _primary_calendar(tenant_id, year_id)
        calendar_id = primary.id

    cal = await AcademicCalendar.get(calendar_id)
    if cal is None or cal.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Calendar not found", status_code=404)

    for event in cal.events:
        event.status = "published"
    cal.updated_at = utcnow()
    await cal.save()

    await publish_calendar(scope, calendar_id)
    await record_audit(
        tenant_id=tenant_id,
        actor_id=scope.user_id,
        action="academic_calendar.published",
        resource_type="academic_calendar",
        resource_id=str(calendar_id),
        metadata={"academic_year_id": str(year_id)},
    )
    return await get_academic_calendar_configuration_page(
        scope,
        academic_year_id=str(year.id),
    )