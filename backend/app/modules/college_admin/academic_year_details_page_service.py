"""Academic year details page (CA 05.02)."""

from __future__ import annotations

from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.academic_config_models import AcademicTerm, AcademicYear, ConfigPublicationStatus
from app.modules.college_admin.academic_year_management_page_service import (
    _format_date,
    _student_counts_by_year,
    _year_status,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AcademicYearDetailsKeyValueRow,
    AcademicYearDetailsPageRead,
    AcademicYearDetailsTermRow,
)

_IST = ZoneInfo("Asia/Kolkata")


async def get_academic_year_details_page(scope: AccessScope, year_id_raw: str) -> AcademicYearDetailsPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_READ)
    tenant_id = require_college_tenant_scope(scope)
    year_id = to_object_id(year_id_raw, "year_id")
    year = await AcademicYear.get(year_id)
    if year is None or year.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Academic year not found", status_code=404)

    today = utcnow().date()
    status_code, status_label, status_tone = _year_status(year, today)
    counts = await _student_counts_by_year(tenant_id)
    student_count = counts.get(year.label, 0)

    terms = await AcademicTerm.find(
        Eq(AcademicTerm.tenant_id, tenant_id),
        Eq(AcademicTerm.academic_year_id, year_id),
    ).sort("+term_code").to_list()

    term_rows: list[AcademicYearDetailsTermRow] = []
    for term in terms:
        start = _format_date(term.start_date)
        end = _format_date(term.end_date)
        period = f"{start} – {end}" if start != "—" or end != "—" else "—"
        if term.is_current:
            term_status, term_tone = "Current", "success"
        elif term.status == ConfigPublicationStatus.PUBLISHED:
            term_status, term_tone = "Published", "info"
        elif term.status == ConfigPublicationStatus.ARCHIVED:
            term_status, term_tone = "Archived", "muted"
        else:
            term_status, term_tone = "Draft", "warning"
        term_rows.append(
            AcademicYearDetailsTermRow(
                term_id=str(term.id),
                label=term.label,
                period_label=period,
                status_label=term_status,
                status_tone=term_tone,
            )
        )

    generated = utcnow()
    snapshot = as_utc_aware(generated).astimezone(_IST).strftime("Live snapshot · %d %b %Y, %H:%M IST")

    overview = [
        AcademicYearDetailsKeyValueRow(key="code", label="Year code", value=year.year_code),
        AcademicYearDetailsKeyValueRow(key="start", label="Start date", value=_format_date(year.start_date)),
        AcademicYearDetailsKeyValueRow(key="end", label="End date", value=_format_date(year.end_date)),
        AcademicYearDetailsKeyValueRow(
            key="intake",
            label="Admission intake opens",
            value=_format_date(year.admission_intake_opens),
        ),
        AcademicYearDetailsKeyValueRow(key="students", label="Enrolled students", value=str(student_count)),
        AcademicYearDetailsKeyValueRow(
            key="summer",
            label="Summer term",
            value=f"{_format_date(year.summer_term_start)} – {_format_date(year.summer_term_end)}",
        ),
        AcademicYearDetailsKeyValueRow(
            key="closing",
            label="Year-end closing",
            value=_format_date(year.year_end_closing),
        ),
    ]

    return AcademicYearDetailsPageRead(
        page_title=year.label,
        page_subtitle="Academic year overview",
        back_href="/college-admin/academics/academic-year-management",
        back_label="All academic years",
        year_id=str(year.id),
        year_label=year.label,
        status_label=status_label,
        status_tone=status_tone,
        is_current=year.is_current,
        overview_section_title="Year details",
        overview_rows=overview,
        terms_section_title="Semesters & terms",
        terms_table_headers=["Term", "Period", "Status"],
        term_rows=term_rows,
        manage_semesters_label="Manage semesters",
        manage_semesters_href=f"/college-admin/academics/semester-management?academic_year_id={year.id}",
        footer_disclaimer="Live academic configuration · Years and terms · All times IST",
        footer_snapshot_label=snapshot,
        generated_at=generated,
    )