"""Student admission list page (CA 06 — Admissions tab)."""

from __future__ import annotations

import math
import re
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.college_admin.academic_config_models import AcademicProgramme, AcademicYear
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    PoliciesPagination,
    StudentAdmissionListTableRow,
    StudentAdmissionPageRead,
    StudentAdminDashboardFilterOption,
    UserDashboardKpi,
)
from app.modules.college_admin.student_admin_models import AdmissionStatus, StudentAdmission, StudentRecord
from app.modules.college_admin.student_administration_dashboard_page_service import (
    _documents_pending_meta,
    _fmt_time_label,
    _quota_label,
)
from app.modules.college_admin.student_statistics_overview_service import (
    _CATEGORY_LABELS,
    _meta_lookup,
    _normalize_meta_key,
)
from app.modules.students.models import StudentProfile

_IST = ZoneInfo("Asia/Kolkata")
_reader = OperationalDataReader()
_PAGE_SIZE = 10

_STATUS_FILTERS: list[tuple[str, str]] = [
    ("", "All statuses"),
    ("approved", "Approved"),
    ("documents_pending", "Documents pending"),
    ("under_review", "Under review"),
    ("rejected", "Rejected"),
    ("withdrawn", "Withdrawn"),
]


def _programme_label(code: str | None, programmes: dict[str, AcademicProgramme]) -> str:
    if not code:
        return "—"
    prog = programmes.get(code.upper())
    if prog and prog.name:
        return prog.name
    return code


def _marks_label(admission: StudentAdmission) -> str:
    raw = _meta_lookup(
        admission.metadata,
        "marks_percentage",
        "entrance_marks",
        "aggregate_marks",
        "percentage",
        "cutoff_marks",
    )
    if raw is None or raw == "":
        return "—"
    try:
        return f"{float(raw):.1f}%"
    except (TypeError, ValueError):
        return str(raw)


def _quota_filter_key(admission: StudentAdmission) -> str:
    raw = _meta_lookup(admission.metadata, "quota", "admission_quota", "category", "seat_category")
    if not raw:
        return ""
    return _normalize_meta_key(str(raw))


def _application_presentation(
    admission: StudentAdmission,
    profile: StudentProfile | None,
) -> tuple[str, str, str]:
    """Return (status_code, status_label, status_tone)."""
    if admission.status == AdmissionStatus.REJECTED:
        return "rejected", "Rejected", "error"
    if admission.status == AdmissionStatus.CANCELLED:
        return "withdrawn", "Withdrawn", "muted"
    if admission.status == AdmissionStatus.CONFIRMED:
        return "approved", "Approved", "success"

    pending_count, _ = _documents_pending_meta(admission)
    if profile:
        pending_count = max(pending_count, sum(1 for ref in profile.document_refs if not ref.authorized))
    review = str(_meta_lookup(admission.metadata, "review_stage", "application_stage") or "").lower()
    if pending_count > 0 or "document" in review:
        return "documents_pending", "Documents pending", "warning"
    return "under_review", "Under review", "info"


def _ay_display(code: str, year_by_code: dict[str, AcademicYear] | None = None) -> str:
    if not code:
        return "—"
    if year_by_code:
        doc = year_by_code.get(code)
        if doc and doc.label:
            return doc.label.replace("-", "–")
    return code.replace("-", "–")


def _academic_year_option_label(year: AcademicYear) -> str:
    label = year.label or year.year_code
    display = label.replace("-", "–")
    if display.upper().startswith("AY "):
        return display
    if display.upper().startswith("AY") or year.year_code.upper().startswith("AY-"):
        return display if display.upper().startswith("AY") else f"AY {display}"
    if "–" in display or re.match(r"^\d{4}", display):
        return f"AY {display}"
    return display


async def get_student_admission_page(
    scope: AccessScope,
    *,
    page: int = 1,
    academic_year_code: str | None = None,
    programme_code: str | None = None,
    quota_filter: str | None = None,
    status_filter: str | None = None,
    search: str | None = None,
) -> StudentAdmissionPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    current_year_label, _ = await _reader.current_academic_term(tenant_id)
    years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-year_code").to_list()
    year_by_code = {y.year_code: y for y in years}
    selected_ay = academic_year_code or current_year_label or (years[0].year_code if years else "")

    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    programme_by_code = {p.programme_code.upper(): p for p in programmes}

    admissions = await StudentAdmission.find(Eq(StudentAdmission.tenant_id, tenant_id)).sort("-created_at").to_list()
    records = await StudentRecord.find(Eq(StudentRecord.tenant_id, tenant_id)).to_list()
    record_by_admission = {r.admission_id: r for r in records if r.admission_id}

    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    profile_by_user = {p.user_id: p for p in profiles}

    ay_options = [StudentAdminDashboardFilterOption(value="", label="All academic years")]
    for year in years:
        ay_options.append(
            StudentAdminDashboardFilterOption(
                value=year.year_code,
                label=_academic_year_option_label(year),
            )
        )
    if selected_ay and not any(o.value == selected_ay for o in ay_options):
        ay_options.append(
            StudentAdminDashboardFilterOption(
                value=selected_ay,
                label=_ay_display(selected_ay, year_by_code),
            )
        )

    quota_keys: set[str] = set(_CATEGORY_LABELS.keys())
    for admission in admissions:
        key = _quota_filter_key(admission)
        if key:
            quota_keys.add(key)

    programme_options = [StudentAdminDashboardFilterOption(value="", label="All programmes")]
    for programme in sorted(programmes, key=lambda p: (p.name or p.programme_code).lower()):
        programme_options.append(
            StudentAdminDashboardFilterOption(
                value=programme.programme_code,
                label=programme.name or programme.programme_code,
            ),
        )

    quota_options = [StudentAdminDashboardFilterOption(value="", label="All quotas")]
    for key in sorted(quota_keys):
        quota_options.append(
            StudentAdminDashboardFilterOption(
                value=key,
                label=_CATEGORY_LABELS.get(key, key.replace("_", " ").title()),
            ),
        )

    programme_q = programme_code.upper() if programme_code else None
    quota_q = _normalize_meta_key(quota_filter) if quota_filter else None
    status_q = (status_filter or "").strip().lower()
    search_q = (search or "").strip().lower()

    scoped = [a for a in admissions if not selected_ay or a.academic_year_code == selected_ay]
    if programme_q:
        scoped = [a for a in scoped if a.programme_code.upper() == programme_q]
    if quota_q:
        scoped = [a for a in scoped if _quota_filter_key(a) == quota_q]

    total_applications = len(scoped)
    pending_apps = [a for a in scoped if a.status == AdmissionStatus.PENDING]
    confirmed_apps = [a for a in scoped if a.status == AdmissionStatus.CONFIRMED]
    rejected_withdrawn = [
        a for a in scoped if a.status in (AdmissionStatus.REJECTED, AdmissionStatus.CANCELLED)
    ]

    docs_pending_count = 0
    for admission in pending_apps:
        profile = profile_by_user.get(admission.confirmed_user_id) if admission.confirmed_user_id else None
        code, _, _ = _application_presentation(admission, profile)
        if code == "documents_pending":
            docs_pending_count += 1

    under_hint = (
        f"{docs_pending_count:,} documents pending"
        if docs_pending_count
        else "Pending admission review"
    )

    kpis = [
        UserDashboardKpi(
            key="applications",
            label="Applications",
            value=f"{total_applications:,}",
            hint_line=f"{_ay_display(selected_ay, year_by_code)} intake" if selected_ay else "All intakes",
            hint_tone="info",
        ),
        UserDashboardKpi(
            key="under_review",
            label="Under review",
            value=f"{len(pending_apps):,}",
            hint_line=under_hint,
            hint_tone="warning" if docs_pending_count else "neutral",
        ),
        UserDashboardKpi(
            key="approved",
            label="Approved",
            value=f"{len(confirmed_apps):,}",
            hint_line="Seats allotted" if confirmed_apps else "No approved applications",
            hint_tone="success" if confirmed_apps else "muted",
        ),
        UserDashboardKpi(
            key="rejected_withdrawn",
            label="Rejected / withdrawn",
            value=f"{len(rejected_withdrawn):,}",
            hint_line="Closed applications",
            hint_tone="muted",
        ),
    ]

    filtered_rows: list[tuple[StudentAdmission, str, str, str, str, str, str]] = []
    for admission in scoped:
        profile = profile_by_user.get(admission.confirmed_user_id) if admission.confirmed_user_id else None
        status_code, status_label, status_tone = _application_presentation(admission, profile)
        if status_q and status_code != status_q:
            continue
        if search_q:
            haystack = " ".join(
                [
                    admission.applicant_name.lower(),
                    admission.admission_number.lower(),
                    admission.applicant_email.lower(),
                ]
            )
            if search_q not in haystack:
                continue

        record = record_by_admission.get(admission.id)
        if record:
            detail_href = f"/college-admin/students/student-details?id={record.id}"
        else:
            detail_href = f"/college-admin/students/new-student-registration?admission_id={admission.id}"

        filtered_rows.append(
            (
                admission,
                _programme_label(admission.programme_code, programme_by_code),
                _quota_label(admission),
                _marks_label(admission),
                status_label,
                status_tone,
                detail_href,
            )
        )

    total = len(filtered_rows)
    total_pages = math.ceil(total / _PAGE_SIZE) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_slice = filtered_rows[start : start + _PAGE_SIZE]

    table_rows: list[StudentAdmissionListTableRow] = []
    for admission, programme_label, quota_label, marks_label, status_label, status_tone, detail_href in page_slice:
        table_rows.append(
            StudentAdmissionListTableRow(
                admission_id=str(admission.id),
                applicant_name=admission.applicant_name.strip() or "Draft application",
                application_number=admission.admission_number,
                programme_label=programme_label,
                quota_label=quota_label,
                marks_label=marks_label,
                status_label=status_label,
                status_tone=status_tone,
                detail_href=detail_href,
            )
        )

    page_numbers = list(range(1, min(total_pages, 12) + 1)) if total_pages else []
    if total_pages > 12:
        page_numbers = [1, 2, 3, -1, total_pages]

    showing_from = start + 1 if total else 0
    showing_to = min(start + _PAGE_SIZE, total)

    subtitle = (
        f"Admission applications for {_ay_display(selected_ay, year_by_code)}"
        if selected_ay
        else "Admission applications for the college"
    )

    return StudentAdmissionPageRead(
        page_title="Student Admission",
        page_subtitle=subtitle,
        export_label="Export",
        new_admission_label="New admission",
        new_admission_href="/college-admin/students/new-student-registration",
        academic_year_filter_label="Academic year",
        programme_filter_label="Programme",
        quota_filter_label="Quota",
        scope_indicator_label="College scope",
        updated_at_label=_fmt_time_label(now),
        academic_year_options=ay_options,
        programme_options=programme_options,
        quota_options=quota_options,
        status_filter_label="Status",
        status_options=[
            StudentAdminDashboardFilterOption(value=v, label=lbl) for v, lbl in _STATUS_FILTERS
        ],
        selected_academic_year=selected_ay,
        selected_programme_code=programme_code or "",
        selected_quota=quota_filter or "",
        selected_status=status_filter or "",
        kpis=kpis,
        applications_section_title="Admission applications",
        applications_count_label=f"{total_applications:,} applications",
        table_headers=["Applicant", "Application no.", "Programme", "Quota", "Marks", "Status"],
        applications=table_rows,
        showing_label=f"Showing {showing_from}–{showing_to} of {total:,}" if total else f"Showing 0 of {total_applications:,}",
        pagination=PoliciesPagination(
            page=page,
            page_size=_PAGE_SIZE,
            total=total,
            total_pages=total_pages,
            page_numbers=page_numbers,
            has_previous=page > 1 and bool(total),
            has_next=page < total_pages,
        ),
        footer_disclaimer="Live institutional data · Student admissions and records · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )