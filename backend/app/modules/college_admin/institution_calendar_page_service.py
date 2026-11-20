"""Institutional calendar settings page (CA — calendar)."""

from __future__ import annotations

import math
from copy import deepcopy
from typing import Any
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.college_admin.academic_config_models import (
    AcademicRegulation,
    AcademicYear,
    ConfigPublicationStatus,
)
from app.modules.college_admin.institution_calendar_models import InstitutionHoliday
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    InstitutionCalendarFormValues,
    InstitutionCalendarHolidayRow,
    InstitutionCalendarSettingsPageRead,
    InstitutionCalendarSettingsSave,
    InstitutionCalendarTimeOption,
    InstitutionCalendarToggleRule,
    InstitutionFieldMeta,
    InstitutionFieldOption,
    PoliciesPagination,
)

_SCOPE_KEY = "institution_calendar_settings"
_HOLIDAY_PAGE_SIZE = 6

_DEFAULT_VALUES: dict[str, Any] = {
    "working_days": "mon_sat",
    "saturday_pattern": "second_fourth_off",
    "day_start": "08:30",
    "day_end": "16:30",
    "publish_student_portal": True,
    "publish_parent_app": True,
    "send_reminders_day_before": True,
    "sync_external_calendars": False,
}

_WORKING_DAY_OPTIONS: list[InstitutionFieldOption] = [
    InstitutionFieldOption(value="mon_sat", label="Mon – Sat"),
    InstitutionFieldOption(value="mon_fri", label="Mon – Fri"),
]

_SATURDAY_PATTERN_OPTIONS: list[InstitutionFieldOption] = [
    InstitutionFieldOption(value="all_working", label="All Saturdays working"),
    InstitutionFieldOption(value="second_fourth_off", label="2nd & 4th Saturday off"),
    InstitutionFieldOption(value="alternate_off", label="Alternate Saturdays off"),
]

_PUBLISHING_TOGGLES: list[tuple[str, str, str | None]] = [
    ("publish_student_portal", "Publish calendar to student portal", None),
    ("publish_parent_app", "Publish to parent app", None),
    ("send_reminders_day_before", "Send reminders 1 day before events", None),
    ("sync_external_calendars", "Sync to Google / Outlook calendars", "iCal feed for staff"),
]

_TYPE_LABELS: dict[str, str] = {
    "gazetted": "Gazetted",
    "national": "National",
    "institution": "Institution",
}

_APPLIES_LABELS: dict[str, str] = {
    "all": "All",
    "students": "Students",
    "staff": "Staff",
    "faculty": "Faculty",
}


def _time_options() -> list[InstitutionCalendarTimeOption]:
    options: list[InstitutionCalendarTimeOption] = []
    for hour in range(6, 21):
        for minute in (0, 30):
            value = f"{hour:02d}:{minute:02d}"
            options.append(InstitutionCalendarTimeOption(value=value, label=value))
    return options


def _format_holiday_date(start: date, end: date | None) -> str:
    if end and end != start:
        if start.year == end.year and start.month == end.month:
            return f"{start.strftime('%d')}–{end.strftime('%d %b %Y')}"
        if start.year == end.year:
            return f"{start.strftime('%d %b')}–{end.strftime('%d %b %Y')}"
        return f"{start.strftime('%d %b %Y')}–{end.strftime('%d %b %Y')}"
    return start.strftime("%d %b %Y")


def _type_label(code: str) -> str:
    return _TYPE_LABELS.get(code.lower(), code.replace("_", " ").title())


def _applies_label(code: str) -> str:
    return _APPLIES_LABELS.get(code.lower(), code.replace("_", " ").title())


async def _current_academic_year(tenant_id: PydanticObjectId) -> AcademicYear | None:
    years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-start_date").to_list()
    current = next((y for y in years if y.is_current), None)
    return current or (years[0] if years else None)


async def _load_settings(tenant_id: PydanticObjectId) -> dict[str, Any]:
    doc = await AcademicRegulation.find_one(
        Eq(AcademicRegulation.tenant_id, tenant_id),
        Eq(AcademicRegulation.scope_key, _SCOPE_KEY),
    )
    if doc is None:
        return deepcopy(_DEFAULT_VALUES)
    return {**_DEFAULT_VALUES, **doc.rules}


def _coerce_form(rules: dict[str, Any]) -> InstitutionCalendarFormValues:
    return InstitutionCalendarFormValues(
        working_days=str(rules.get("working_days", _DEFAULT_VALUES["working_days"])),
        saturday_pattern=str(rules.get("saturday_pattern", _DEFAULT_VALUES["saturday_pattern"])),
        day_start=str(rules.get("day_start", _DEFAULT_VALUES["day_start"])),
        day_end=str(rules.get("day_end", _DEFAULT_VALUES["day_end"])),
        publish_student_portal=bool(rules.get("publish_student_portal", True)),
        publish_parent_app=bool(rules.get("publish_parent_app", True)),
        send_reminders_day_before=bool(rules.get("send_reminders_day_before", True)),
        sync_external_calendars=bool(rules.get("sync_external_calendars", False)),
    )


async def _persist_settings(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    rules: dict[str, Any],
) -> None:
    doc = await AcademicRegulation.find_one(
        Eq(AcademicRegulation.tenant_id, tenant_id),
        Eq(AcademicRegulation.scope_key, _SCOPE_KEY),
    )
    if doc is None:
        doc = AcademicRegulation(
            tenant_id=tenant_id,
            scope_key=_SCOPE_KEY,
            rules=rules,
            status=ConfigPublicationStatus.PUBLISHED,
            updated_by=scope.user_id,
        )
        await doc.insert()
        return
    doc.rules = rules
    doc.status = ConfigPublicationStatus.PUBLISHED
    doc.version += 1
    doc.updated_at = utcnow()
    doc.updated_by = scope.user_id
    await doc.save()


async def get_institution_calendar_settings_page(
    scope: AccessScope,
    *,
    page: int = 1,
    academic_year_id: str | None = None,
) -> InstitutionCalendarSettingsPageRead:
    authorize(scope, Permission.INSTITUTION_SETTINGS_READ)
    tenant_id = require_college_tenant_scope(scope)
    year = None
    if academic_year_id:
        year = await AcademicYear.get(PydanticObjectId(academic_year_id))
        if year is None or year.tenant_id != tenant_id:
            year = None
    if year is None:
        year = await _current_academic_year(tenant_id)

    rules = await _load_settings(tenant_id)
    form = _coerce_form(rules)
    toggles = [
        InstitutionCalendarToggleRule(
            key=key,
            label=label,
            description=description,
            enabled=bool(getattr(form, key)),
        )
        for key, label, description in _PUBLISHING_TOGGLES
    ]

    holidays_total = 0
    holiday_rows: list[InstitutionCalendarHolidayRow] = []
    holidays_section_title = "Holidays"
    holiday_count_label = "0 holidays"
    total_pages = 0
    page_numbers: list[int] = []

    if year:
        holidays_section_title = f"Holidays – {year.label}"
        filters = [
            Eq(InstitutionHoliday.tenant_id, tenant_id),
            Eq(InstitutionHoliday.academic_year_id, year.id),
        ]
        holidays_total = await InstitutionHoliday.find(*filters).count()
        total_pages = max(1, math.ceil(holidays_total / _HOLIDAY_PAGE_SIZE)) if holidays_total else 0
        page = min(max(1, page), total_pages or 1)
        offset = (page - 1) * _HOLIDAY_PAGE_SIZE
        rows = (
            await InstitutionHoliday.find(*filters)
            .sort("+start_date", "+sort_order")
            .skip(offset)
            .limit(_HOLIDAY_PAGE_SIZE)
            .to_list()
        )
        holiday_rows = [
            InstitutionCalendarHolidayRow(
                holiday_id=row.holiday_id,
                title=row.title,
                date_label=_format_holiday_date(row.start_date, row.end_date),
                type_label=_type_label(row.holiday_type),
                applies_to_label=_applies_label(row.applies_to),
            )
            for row in rows
        ]
        holiday_count_label = f"{holidays_total} holiday{'s' if holidays_total != 1 else ''} this year"
        if total_pages > 0:
            page_numbers = list(range(1, min(total_pages, 12) + 1))
            if total_pages > 12:
                page_numbers = [1, 2, 3, -1, total_pages]
        else:
            page_numbers = []

    pagination = PoliciesPagination(
        page=page if year and holidays_total else 1,
        page_size=_HOLIDAY_PAGE_SIZE,
        total=holidays_total,
        total_pages=total_pages,
        page_numbers=page_numbers,
        has_previous=page > 1 and bool(holidays_total),
        has_next=page < total_pages,
    )

    return InstitutionCalendarSettingsPageRead(
        page_title="Institutional Calendar Settings",
        page_subtitle="Working days, holidays and calendar publishing rules",
        import_holidays_label="Import holidays",
        save_label="Save settings",
        cancel_label="Cancel",
        holidays_section_title=holidays_section_title,
        add_holiday_label="Add holiday",
        add_holiday_href="/college-admin/institution/calendar#add-holiday",
        holiday_table_headers=["Holiday", "Date", "Type", "Applies to"],
        holidays=holiday_rows,
        holiday_count_label=holiday_count_label,
        pagination=pagination,
        selected_academic_year_id=str(year.id) if year else None,
        working_week_title="Working week",
        publishing_title="Publishing",
        form=form,
        working_days_options=_WORKING_DAY_OPTIONS,
        saturday_pattern_options=_SATURDAY_PATTERN_OPTIONS,
        time_options=_time_options(),
        working_days_meta=InstitutionFieldMeta(
            key="working_days",
            label="Working days",
            required=True,
            field_type="select",
        ),
        saturday_pattern_meta=InstitutionFieldMeta(
            key="saturday_pattern",
            label="Saturday pattern",
            required=False,
            field_type="select",
        ),
        day_start_meta=InstitutionFieldMeta(key="day_start", label="Day start", required=True, field_type="select"),
        day_end_meta=InstitutionFieldMeta(key="day_end", label="Day end", required=True, field_type="select"),
        publishing_toggles=toggles,
        footer_note="Changes are saved to the audit log with your name and time.",
        footer_disclaimer="Live institutional calendar data · Holidays stored per academic year · All times IST",
        footer_snapshot_label="Live snapshot",
        generated_at=utcnow(),
    )


async def save_institution_calendar_settings_page(
    scope: AccessScope,
    payload: InstitutionCalendarSettingsSave,
) -> InstitutionCalendarSettingsPageRead:
    authorize(scope, Permission.INSTITUTION_SETTINGS_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    rules = payload.form.model_dump(mode="json")
    await _persist_settings(scope, tenant_id, rules)
    await record_audit(
        actor_id=scope.user_id,
        action="institution.calendar_settings.updated",
        resource_type="academic_regulation",
        resource_id=_SCOPE_KEY,
        tenant_id=tenant_id,
    )
    return await get_institution_calendar_settings_page(
        scope,
        page=payload.page,
        academic_year_id=payload.academic_year_id,
    )


async def import_institution_holidays_from_previous(scope: AccessScope) -> InstitutionCalendarSettingsPageRead:
    authorize(scope, Permission.INSTITUTION_SETTINGS_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    current = await _current_academic_year(tenant_id)
    if current is None:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Create an academic year before importing holidays",
            status_code=422,
        )
    years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-start_date").to_list()
    previous = next((y for y in years if y.id != current.id), None)
    if previous is None:
        raise AppError(code="NOT_FOUND", message="No previous academic year to import from", status_code=404)

    existing = await InstitutionHoliday.find(
        Eq(InstitutionHoliday.tenant_id, tenant_id),
        Eq(InstitutionHoliday.academic_year_id, current.id),
    ).count()
    if existing:
        raise AppError(
            code="CONFLICT",
            message="Current year already has holidays; clear or add manually",
            status_code=409,
        )

    source_rows = await InstitutionHoliday.find(
        Eq(InstitutionHoliday.tenant_id, tenant_id),
        Eq(InstitutionHoliday.academic_year_id, previous.id),
    ).sort("+start_date").to_list()

    for row in source_rows:
        await InstitutionHoliday(
            tenant_id=tenant_id,
            academic_year_id=current.id,
            holiday_id=f"{row.holiday_id}-{uuid4().hex[:6]}",
            title=row.title,
            start_date=row.start_date,
            end_date=row.end_date,
            holiday_type=row.holiday_type,
            applies_to=row.applies_to,
            sort_order=row.sort_order,
        ).insert()

    await record_audit(
        actor_id=scope.user_id,
        action="institution.calendar_holidays.imported",
        resource_type="institution_holiday",
        resource_id=str(current.id),
        tenant_id=tenant_id,
    )
    return await get_institution_calendar_settings_page(scope, academic_year_id=str(current.id))