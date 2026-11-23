"""Institution academic year configuration page (CA 02.x)."""

from __future__ import annotations

from datetime import date
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
    AcademicCalendar,
    AcademicTerm,
    AcademicYear,
    ConfigPublicationStatus,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AcademicYearConfigurationPageRead,
    AcademicYearConfigurationSave,
    AcademicYearLinkedConfig,
    AcademicYearSemesterForm,
    AcademicYearSemesterFieldMeta,
    AcademicYearTableRow,
    AcademicYearTimelineItem,
)
from app.modules.college_admin.student_admin_models import StudentAdmission


def _format_date(value: date | None) -> str:
    if value is None:
        return "—"
    return value.strftime("%d %b %Y")


def _format_range(start: date | None, end: date | None) -> str:
    if start and end:
        return f"{start.strftime('%d %b')} - {end.strftime('%d %b %Y')}"
    if start:
        return _format_date(start)
    return "—"


def _year_status(year: AcademicYear, today: date) -> tuple[str, str, str]:
    if year.is_current:
        return "current", "Current", "success"
    if year.status == ConfigPublicationStatus.ARCHIVED:
        return "archived", "Archived", "muted"
    if year.end_date and year.end_date < today:
        return "closed", "Closed", "muted"
    if year.status == ConfigPublicationStatus.PUBLISHED:
        return "published", "Published", "info"
    return "draft", "Draft", "warning"


def _timeline_status(event_date: date, today: date) -> tuple[str, str]:
    if event_date < today:
        return "done", "Done"
    return "upcoming", "Upcoming"


async def _upsert_term(
    tenant_id: PydanticObjectId,
    year_id: PydanticObjectId,
    term_code: str,
    label: str,
    start: date | None,
    end: date | None,
) -> None:
    code = term_code.upper()
    existing = await AcademicTerm.find_one(
        Eq(AcademicTerm.tenant_id, tenant_id),
        Eq(AcademicTerm.academic_year_id, year_id),
        Eq(AcademicTerm.term_code, code),
    )
    if existing:
        existing.start_date = start
        existing.end_date = end
        existing.label = label
        existing.updated_at = utcnow()
        await existing.save()
        return
    await AcademicTerm(
        tenant_id=tenant_id,
        academic_year_id=year_id,
        term_code=code,
        label=label,
        start_date=start,
        end_date=end,
    ).insert()


async def _semesters_label(terms: list[AcademicTerm]) -> str:
    if not terms:
        return "—"
    labels = [t.label for t in sorted(terms, key=lambda row: row.term_code)]
    return ", ".join(labels)


async def _build_timeline(
    year: AcademicYear,
    terms: list[AcademicTerm],
    calendars: list[AcademicCalendar],
    today: date,
) -> list[AcademicYearTimelineItem]:
    items: list[tuple[date, AcademicYearTimelineItem]] = []
    for term in terms:
        if term.start_date:
            status_code, status_label = _timeline_status(term.start_date, today)
            title = f"{term.label} classes begin"
            items.append(
                (
                    term.start_date,
                    AcademicYearTimelineItem(
                        item_id=f"term-start-{term.term_code}",
                        title=title,
                        date_label=_format_date(term.start_date),
                        status_code=status_code,
                        status_label=status_label,
                        status_tone="success" if status_code == "done" else "info",
                    ),
                )
            )
    for calendar in calendars:
        for event in calendar.events:
            event_date = event.event_at.date()
            status_code, status_label = _timeline_status(event_date, today)
            tone = "success" if status_code == "done" else "info"
            if "exam" in event.event_type.lower() or "exam" in event.title.lower():
                label = event.title
                if event.description:
                    label = f"{event.title} · {event.description}"
                items.append(
                    (
                        event_date,
                        AcademicYearTimelineItem(
                            item_id=f"cal-{calendar.id}-{event.title[:20]}",
                            title=label,
                            date_label=_format_date(event_date),
                            status_code=status_code,
                            status_label=status_label,
                            status_tone=tone,
                        ),
                    )
                )
    if year.year_end_closing:
        status_code, status_label = _timeline_status(year.year_end_closing, today)
        items.append(
            (
                year.year_end_closing,
                AcademicYearTimelineItem(
                    item_id="year-close",
                    title="Academic year closes",
                    date_label=_format_date(year.year_end_closing),
                    status_code=status_code,
                    status_label=status_label if status_code == "done" else "",
                    status_tone="muted" if status_code != "done" else "success",
                ),
            )
        )
    items.sort(key=lambda pair: pair[0])
    return [item for _, item in items[:12]]


async def get_academic_year_configuration_page(
    scope: AccessScope,
    *,
    selected_year_id: str | None = None,
) -> AcademicYearConfigurationPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_READ)
    tenant_id = require_college_tenant_scope(scope)
    today = utcnow().date()

    years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-start_date").to_list()
    table_rows: list[AcademicYearTableRow] = []
    for year in years:
        terms = await AcademicTerm.find(
            Eq(AcademicTerm.tenant_id, tenant_id),
            Eq(AcademicTerm.academic_year_id, year.id),
        ).to_list()
        code, label, tone = _year_status(year, today)
        table_rows.append(
            AcademicYearTableRow(
                year_id=str(year.id),
                label=year.label,
                start_label=_format_date(year.start_date),
                end_label=_format_date(year.end_date),
                semesters_label=await _semesters_label(terms),
                status_code=code,
                status_label=label,
                status_tone=tone,
            )
        )

    selected: AcademicYear | None = None
    if selected_year_id:
        selected = await AcademicYear.get(PydanticObjectId(selected_year_id))
        if selected is None or selected.tenant_id != tenant_id:
            selected = None
    if selected is None:
        selected = next((y for y in years if y.is_current), years[0] if years else None)

    semester_form: AcademicYearSemesterForm | None = None
    timeline: list[AcademicYearTimelineItem] = []
    linked: list[AcademicYearLinkedConfig] = []
    semester_section_title = "Semesters"

    if selected:
        terms = await AcademicTerm.find(
            Eq(AcademicTerm.tenant_id, tenant_id),
            Eq(AcademicTerm.academic_year_id, selected.id),
        ).to_list()
        term_by_code = {t.term_code.upper(): t for t in terms}
        odd = term_by_code.get("ODD")
        even = term_by_code.get("EVEN")
        semester_section_title = f"{selected.label} semesters"
        semester_form = AcademicYearSemesterForm(
            odd_semester_start=odd.start_date if odd else None,
            odd_semester_end=odd.end_date if odd else None,
            even_semester_start=even.start_date if even else None,
            even_semester_end=even.end_date if even else None,
            summer_term_start=selected.summer_term_start,
            summer_term_end=selected.summer_term_end,
            year_end_closing=selected.year_end_closing,
        )
        calendars = await AcademicCalendar.find(
            Eq(AcademicCalendar.tenant_id, tenant_id),
            Eq(AcademicCalendar.academic_year_id, selected.id),
        ).to_list()
        timeline = await _build_timeline(selected, terms, calendars, today)
        event_count = sum(len(c.events) for c in calendars)
        admissions = await StudentAdmission.find(
            Eq(StudentAdmission.tenant_id, tenant_id),
        ).to_list()
        intake_labels = sorted(
            {row.batch_label for row in admissions if row.batch_label},
            reverse=True,
        )
        batch_hint = intake_labels[0] if intake_labels else "No intake batches"
        linked = [
            AcademicYearLinkedConfig(
                key="academic_calendar",
                title="Academic calendar",
                description=f"{event_count} events",
                href="/college-admin/academics/academic-configuration-dashboard",
                icon_slug="calendar",
            ),
            AcademicYearLinkedConfig(
                key="batches_sections",
                title="Batches & sections",
                description=batch_hint,
                href="/college-admin/academics/batch-section-configuration",
                icon_slug="users",
            ),
        ]

    return AcademicYearConfigurationPageRead(
        page_title="Academic Year Configuration",
        page_subtitle="Define academic years, semesters and their key dates",
        copy_from_previous_label="Copy from previous year",
        new_academic_year_label="New academic year",
        save_label="Save configuration",
        cancel_label="Cancel",
        academic_years_table_title="Academic years",
        archive_view_href="/college-admin/academics/academic-year-management",
        archive_view_label="View archive →",
        academic_year_count_label=f"{len(years)} academic year{'s' if len(years) != 1 else ''}",
        academic_years=table_rows,
        selected_year_id=str(selected.id) if selected else None,
        semester_section_title=semester_section_title,
        semester_form=semester_form,
        semester_field_meta=[
            AcademicYearSemesterFieldMeta(key="odd_semester_start", label="Odd semester start", required=True),
            AcademicYearSemesterFieldMeta(key="odd_semester_end", label="Odd semester end", required=True),
            AcademicYearSemesterFieldMeta(key="even_semester_start", label="Even semester start", required=True),
            AcademicYearSemesterFieldMeta(key="even_semester_end", label="Even semester end", required=True),
            AcademicYearSemesterFieldMeta(key="summer_term", label="Summer term", required=False, field_type="range"),
            AcademicYearSemesterFieldMeta(key="year_end_closing", label="Year-end closing", required=False),
        ],
        year_timeline_title="Year timeline",
        timeline=timeline,
        linked_configuration_title="Linked configuration",
        linked_configuration=linked,
        footer_disclaimer=(
            "Live academic configuration · Years, terms and calendar events · All times IST"
        ),
        footer_snapshot_label="Live snapshot",
        generated_at=utcnow(),
    )


async def save_academic_year_configuration(
    scope: AccessScope,
    year_id: PydanticObjectId,
    payload: AcademicYearConfigurationSave,
) -> AcademicYearConfigurationPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    year = await AcademicYear.get(year_id)
    if year is None or year.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Academic year not found", status_code=404)
    if year.status == ConfigPublicationStatus.PUBLISHED:
        raise AppError(code="FORBIDDEN", message="Published academic years are immutable", status_code=403)

    from app.modules.college_admin.form_validation_details import raise_validation_error, scroll_field

    form = payload.semester_form
    details: list[dict] = []
    if not form.odd_semester_start:
        details.append(
            scroll_field("odd_semester_start", label="Odd semester start", message="Select the odd semester start date.")
        )
    if not form.odd_semester_end:
        details.append(
            scroll_field("odd_semester_end", label="Odd semester end", message="Select the odd semester end date.")
        )
    if not form.even_semester_start:
        details.append(
            scroll_field("even_semester_start", label="Even semester start", message="Select the even semester start date.")
        )
    if not form.even_semester_end:
        details.append(
            scroll_field("even_semester_end", label="Even semester end", message="Select the even semester end date.")
        )
    if details:
        raise_validation_error("Complete all semester dates before saving.", details)
    if form.odd_semester_end < form.odd_semester_start:
        raise_validation_error(
            "Check the odd semester date range.",
            [
                scroll_field(
                    "odd_semester_end",
                    label="Odd semester end",
                    message="End date must be on or after the start date.",
                )
            ],
        )
    if form.even_semester_end < form.even_semester_start:
        raise_validation_error(
            "Check the even semester date range.",
            [
                scroll_field(
                    "even_semester_end",
                    label="Even semester end",
                    message="End date must be on or after the start date.",
                )
            ],
        )
    await _upsert_term(tenant_id, year.id, "ODD", "Odd", form.odd_semester_start, form.odd_semester_end)
    await _upsert_term(tenant_id, year.id, "EVEN", "Even", form.even_semester_start, form.even_semester_end)
    year.summer_term_start = form.summer_term_start
    year.summer_term_end = form.summer_term_end
    year.year_end_closing = form.year_end_closing
    if year.start_date is None and form.odd_semester_start:
        year.start_date = form.odd_semester_start
    if year.end_date is None and form.year_end_closing:
        year.end_date = form.year_end_closing
    year.updated_at = utcnow()
    year.updated_by = scope.user_id
    year.version += 1
    await year.save()

    await record_audit(
        actor_id=scope.user_id,
        action="institution.academic_year.configuration.saved",
        resource_type="academic_year",
        resource_id=str(year.id),
        tenant_id=tenant_id,
    )
    return await get_academic_year_configuration_page(scope, selected_year_id=str(year.id))


async def copy_academic_year_from_previous(scope: AccessScope) -> AcademicYearConfigurationPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-start_date").to_list()
    if not years:
        raise AppError(code="NOT_FOUND", message="No academic year to copy from", status_code=404)
    source = years[0]
    suffix = uuid4().hex[:4].upper()
    new_year = AcademicYear(
        tenant_id=tenant_id,
        year_code=f"{source.year_code}-COPY-{suffix}",
        label=f"{source.label} (copy)",
        start_date=source.start_date,
        end_date=source.end_date,
        summer_term_start=source.summer_term_start,
        summer_term_end=source.summer_term_end,
        year_end_closing=source.year_end_closing,
        is_current=False,
        updated_by=scope.user_id,
    )
    await new_year.insert()
    source_terms = await AcademicTerm.find(
        Eq(AcademicTerm.tenant_id, tenant_id),
        Eq(AcademicTerm.academic_year_id, source.id),
    ).to_list()
    for term in source_terms:
        await AcademicTerm(
            tenant_id=tenant_id,
            academic_year_id=new_year.id,
            term_code=term.term_code,
            label=term.label,
            start_date=term.start_date,
            end_date=term.end_date,
        ).insert()
    return await get_academic_year_configuration_page(scope, selected_year_id=str(new_year.id))


async def create_blank_academic_year(scope: AccessScope) -> AcademicYearConfigurationPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    code = f"AY-{uuid4().hex[:6].upper()}"
    doc = AcademicYear(
        tenant_id=tenant_id,
        year_code=code,
        label="New academic year",
        updated_by=scope.user_id,
    )
    await doc.insert()
    return await get_academic_year_configuration_page(scope, selected_year_id=str(doc.id))