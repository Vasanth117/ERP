"""Student administration overview dashboard (CA 06.01)."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, GTE

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import as_utc_aware, utcnow
from app.modules.college_admin.academic_config_models import AcademicProgramme, AcademicYear
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    StudentAdminDashboardFilterOption,
    StudentAdminDocumentAlert,
    StudentAdminEnrollmentYearBar,
    StudentAdminRecentAdmissionRow,
    StudentAdminStatusItem,
    StudentAdminWeeklySeriesPoint,
    StudentAdminWorkQueueItem,
    StudentAdministrationDashboardPageRead,
    UserDashboardKpi,
)
from app.modules.college_admin.student_admin_models import (
    AdmissionStatus,
    StudentAdmission,
    StudentLifecycleStatus,
    StudentRecord,
    StudentStatusHistory,
    StudentTransfer,
    TransferStatus,
)
from app.modules.college_admin.student_statistics_overview_service import (
    _CATEGORY_LABELS,
    _ENROLLED_LIFECYCLE,
    _academic_year_start,
    _meta_lookup,
    _normalize_meta_key,
    _previous_academic_year_label,
    _programme_group_key,
    _study_year,
)
from app.modules.department_admin.models import DepartmentRequestStatus, DepartmentSectionTransferRequest
from app.modules.students.enums import AcademicStanding
from app.modules.students.models import StudentAcademicRecord, StudentProfile

_IST = ZoneInfo("Asia/Kolkata")
_reader = OperationalDataReader()
_DOCUMENT_OVERDUE_DAYS = 30
_WEEK_COUNT = 8

_YEAR_BUCKETS: tuple[tuple[str, str, int | None, int | None], ...] = (
    ("y1", "Year 1", 1, 1),
    ("y2", "Year 2", 2, 2),
    ("y3", "Year 3", 3, 3),
    ("y4", "Year 4", 4, 4),
    ("pg_phd", "PG & Ph.D.", 5, None),
)


def _fmt_admitted(when: datetime) -> str:
    return as_utc_aware(when).astimezone(_IST).strftime("%d %b")


def _fmt_time_label(now: datetime) -> str:
    return now.astimezone(_IST).strftime("Updated %H:%M IST")


def _documents_pending_meta(admission: StudentAdmission) -> tuple[int, str | None]:
    meta = admission.metadata or {}
    if meta.get("documents_verified") is True:
        return 0, None
    pending = meta.get("pending_documents_count")
    if pending is None:
        pending = meta.get("pending_documents")
    if isinstance(pending, list):
        return len(pending), meta.get("pending_document_label") or meta.get("document_issue")
    if isinstance(pending, (int, float)):
        return int(pending), meta.get("pending_document_label") or meta.get("document_issue")
    if meta.get("documents_verified") is False:
        return 1, meta.get("pending_document_label") or meta.get("document_issue")
    issue = meta.get("document_issue") or meta.get("pending_document_label")
    if issue:
        return 1, str(issue)
    return 0, None


def _documents_status(
    admission: StudentAdmission,
    profile: StudentProfile | None,
) -> tuple[str, str, int]:
    pending_count, issue_label = _documents_pending_meta(admission)
    if profile:
        unauthorized = sum(1 for ref in profile.document_refs if not ref.authorized)
        pending_count = max(pending_count, unauthorized)
        if unauthorized and not issue_label:
            issue_label = f"{unauthorized} pending"
    if pending_count <= 0:
        return "Verified", "success", 0
    label = issue_label if issue_label and len(str(issue_label)) <= 36 else f"{pending_count} pending"
    tone = "error" if issue_label and any(tok in str(issue_label).lower() for tok in ("missing", "tc", "reject")) else "warning"
    return str(label), tone, pending_count


def _quota_label(admission: StudentAdmission) -> str:
    raw = _meta_lookup(admission.metadata, "quota", "admission_quota", "category", "seat_category")
    if not raw:
        return "—"
    key = _normalize_meta_key(raw)
    return _CATEGORY_LABELS.get(key, raw.replace("_", " ").title())


def _programme_label(code: str | None, programmes: dict[str, AcademicProgramme]) -> str:
    if not code:
        return "—"
    prog = programmes.get(code)
    if prog and prog.name:
        return prog.name
    return code


def _record_matches_filters(
    record: StudentRecord,
    *,
    programme_code: str | None,
    study_year: int | None,
    ay_label: str | None,
    admission_by_id: dict[PydanticObjectId, StudentAdmission],
) -> bool:
    if programme_code and (record.programme_code or "").upper() != programme_code.upper():
        return False
    if ay_label:
        admission = admission_by_id.get(record.admission_id) if record.admission_id else None
        if admission and admission.academic_year_code != ay_label:
            return False
    if study_year is not None:
        computed = _study_year(record.batch_label, ay_label)
        if computed is None or computed != study_year:
            return False
    return True


def _display_academic_year(code: str, year_by_code: dict[str, AcademicYear]) -> str:
    doc = year_by_code.get(code)
    raw = doc.label if doc and doc.label else code
    return raw.replace("-", "–")


def _prior_academic_year_code(years: list[AcademicYear], selected: str) -> str | None:
    if not selected:
        return None
    parsed = _previous_academic_year_label(selected)
    if parsed and any(y.year_code == parsed for y in years):
        return parsed
    for index, year in enumerate(years):
        if year.year_code == selected and index + 1 < len(years):
            return years[index + 1].year_code
    return None


def _admission_anchor(academic_year: AcademicYear | None, ay_label: str) -> date:
    if academic_year:
        if academic_year.admission_intake_opens:
            return academic_year.admission_intake_opens
        if academic_year.start_date:
            return academic_year.start_date
    start_year = _academic_year_start(ay_label) or utcnow().year
    return date(start_year, 6, 1)


def _admission_week(admission_date: date, anchor: date) -> int | None:
    if admission_date < anchor:
        return None
    week = (admission_date - anchor).days // 7 + 1
    return week if 1 <= week <= _WEEK_COUNT else None


async def get_student_administration_dashboard_page(
    scope: AccessScope,
    *,
    academic_year_code: str | None = None,
    programme_code: str | None = None,
    study_year: int | None = None,
) -> StudentAdministrationDashboardPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    current_year_label, _ = await _reader.current_academic_term(tenant_id)
    years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-year_code").to_list()
    year_by_code = {y.year_code: y for y in years}
    selected_ay = academic_year_code or current_year_label or (years[0].year_code if years else "")
    academic_year_doc = year_by_code.get(selected_ay)

    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    programme_by_code = {p.programme_code: p for p in programmes}

    records = await StudentRecord.find(Eq(StudentRecord.tenant_id, tenant_id)).to_list()
    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    profile_by_user = {p.user_id: p for p in profiles}
    admissions = await StudentAdmission.find(Eq(StudentAdmission.tenant_id, tenant_id)).to_list()
    admission_by_id = {a.id: a for a in admissions if a.id is not None}

    filtered_records = [
        r
        for r in records
        if _record_matches_filters(
            r,
            programme_code=programme_code,
            study_year=study_year,
            ay_label=selected_ay or None,
            admission_by_id=admission_by_id,
        )
    ]
    enrolled_records = [
        r for r in filtered_records if r.lifecycle_status.value in _ENROLLED_LIFECYCLE
    ]
    total_enrolled = len(enrolled_records)

    prev_label = _prior_academic_year_code(years, selected_ay) if selected_ay else None
    prev_enrolled = 0
    if prev_label:
        prev_enrolled = sum(
            1
            for r in records
            if r.lifecycle_status.value in _ENROLLED_LIFECYCLE
            and r.admission_id
            and admission_by_id.get(r.admission_id)
            and admission_by_id[r.admission_id].academic_year_code == prev_label
        )
    enrolled_hint = (
        f"{((total_enrolled - prev_enrolled) / prev_enrolled * 100):+.1f}% vs {prev_label}"
        if prev_enrolled > 0
        else "Enrolled students in scope"
    )
    enrolled_hint_tone = "success" if prev_enrolled > 0 and total_enrolled >= prev_enrolled else "neutral"

    admissions_scope = [
        a for a in admissions if not selected_ay or a.academic_year_code == selected_ay
    ]
    if programme_code:
        admissions_scope = [a for a in admissions_scope if a.programme_code.upper() == programme_code.upper()]
    confirmed_admissions = [a for a in admissions_scope if a.status == AdmissionStatus.CONFIRMED]
    admissions_count = len(confirmed_admissions)

    sanctioned = 0
    for admission in admissions_scope:
        intake = admission.metadata.get("sanctioned_intake") or admission.metadata.get("intake")
        if isinstance(intake, (int, float)):
            sanctioned += int(intake)
    admissions_hint = (
        f"{round((admissions_count / sanctioned) * 100)}% of sanctioned intake"
        if sanctioned > 0
        else "Confirmed admissions in scope"
    )

    documents_pending = 0
    verification_overdue = 0
    overdue_cutoff = now - timedelta(days=_DOCUMENT_OVERDUE_DAYS)
    record_by_admission = {r.admission_id: r for r in records if r.admission_id}
    for admission in confirmed_admissions:
        profile = profile_by_user.get(admission.confirmed_user_id) if admission.confirmed_user_id else None
        _, _, pending = _documents_status(admission, profile)
        if pending > 0:
            documents_pending += 1
            if as_utc_aware(admission.created_at) < overdue_cutoff:
                verification_overdue += 1

    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    status_changes = await StudentStatusHistory.find(
        Eq(StudentStatusHistory.tenant_id, tenant_id),
        GTE(StudentStatusHistory.created_at, month_start),
    ).count()

    unassigned_sections = sum(
        1
        for r in enrolled_records
        if not (r.section_code or "").strip()
    )
    transfer_requests = await StudentTransfer.find(
        Eq(StudentTransfer.tenant_id, tenant_id),
        Eq(StudentTransfer.status, TransferStatus.REQUESTED),
    ).count()
    section_transfers = await DepartmentSectionTransferRequest.find(
        Eq(DepartmentSectionTransferRequest.tenant_id, tenant_id),
        Eq(DepartmentSectionTransferRequest.status, DepartmentRequestStatus.PENDING),
    ).count()
    transfer_total = transfer_requests + section_transfers

    id_cards_pending = sum(
        1
        for r in enrolled_records
        if (prof := profile_by_user.get(r.user_id)) is not None and not prof.profile_photo_ref
    )

    academic_records = await StudentAcademicRecord.find(Eq(StudentAcademicRecord.tenant_id, tenant_id)).to_list()
    detained_users = {ar.user_id for ar in academic_records if ar.academic_standing in (AcademicStanding.PROBATION, AcademicStanding.SUSPENDED)}

    active_count = sum(1 for r in enrolled_records if r.lifecycle_status == StudentLifecycleStatus.ACTIVE)
    on_leave = sum(1 for r in enrolled_records if r.lifecycle_status == StudentLifecycleStatus.ON_LEAVE)
    discontinued = sum(
        1
        for r in filtered_records
        if r.lifecycle_status in (StudentLifecycleStatus.DISCONTINUED, StudentLifecycleStatus.WITHDRAWN)
    )
    detained = sum(1 for r in enrolled_records if r.user_id in detained_users)

    year_counts: dict[str, int] = defaultdict(int)
    for record in enrolled_records:
        profile = profile_by_user.get(record.user_id)
        study = _study_year(record.batch_label, selected_ay)
        prog_key = _programme_group_key(record.programme_code, profile.programme_name if profile else None)
        if prog_key == "phd" or (study is not None and study >= 5):
            year_counts["pg_phd"] += 1
        elif study is not None and 1 <= study <= 4:
            year_counts[f"y{study}"] += 1
        else:
            year_counts["y1"] += 1
    max_year = max(year_counts.values()) if year_counts else 1
    enrollment_bars = [
        StudentAdminEnrollmentYearBar(
            year_key=key,
            year_label=label,
            student_count=year_counts.get(key, 0),
            share_percent=round((year_counts.get(key, 0) / max_year) * 100) if max_year else 0,
        )
        for key, label, _lo, _hi in _YEAR_BUCKETS
    ]

    prev_ay = prev_label
    current_anchor = _admission_anchor(academic_year_doc, selected_ay)
    prev_year_doc = year_by_code.get(prev_ay) if prev_ay else None
    prev_anchor = _admission_anchor(prev_year_doc, prev_ay) if prev_ay else current_anchor

    weekly_current: dict[int, int] = defaultdict(int)
    weekly_prev: dict[int, int] = defaultdict(int)
    for admission in admissions:
        if admission.status != AdmissionStatus.CONFIRMED:
            continue
        admitted_on = as_utc_aware(admission.created_at).astimezone(_IST).date()
        if admission.academic_year_code == selected_ay:
            week = _admission_week(admitted_on, current_anchor)
            if week:
                weekly_current[week] += 1
        elif prev_ay and admission.academic_year_code == prev_ay:
            week = _admission_week(admitted_on, prev_anchor)
            if week:
                weekly_prev[week] += 1

    weekly_series = [
        StudentAdminWeeklySeriesPoint(
            week_label=f"Week {i}",
            current_year_count=weekly_current.get(i, 0),
            previous_year_count=weekly_prev.get(i, 0),
        )
        for i in range(1, _WEEK_COUNT + 1)
    ]

    recent_source = sorted(confirmed_admissions, key=lambda a: a.created_at, reverse=True)[:5]
    recent_rows: list[StudentAdminRecentAdmissionRow] = []
    for admission in recent_source:
        profile = profile_by_user.get(admission.confirmed_user_id) if admission.confirmed_user_id else None
        doc_label, doc_tone, _ = _documents_status(admission, profile)
        linked_record = record_by_admission.get(admission.id)
        if linked_record and linked_record.id:
            detail_href = f"/college-admin/students/student-details?id={linked_record.id}"
        else:
            detail_href = "/college-admin/students/student-admission"
        recent_rows.append(
            StudentAdminRecentAdmissionRow(
                admission_id=str(admission.id),
                student_name=admission.applicant_name,
                programme_label=_programme_label(admission.programme_code, programme_by_code),
                quota_label=_quota_label(admission),
                admitted_label=_fmt_admitted(admission.created_at),
                documents_status_label=doc_label,
                documents_status_tone=doc_tone,
                detail_href=detail_href,
            )
        )

    document_alert = None
    if verification_overdue > 0:
        document_alert = StudentAdminDocumentAlert(
            title="Document verification overdue",
            description=(
                f"{verification_overdue} admitted student{'s' if verification_overdue != 1 else ''} "
                f"have unverified documents past the {_DOCUMENT_OVERDUE_DAYS}-day deadline. "
                "Review and verify outstanding files before enrollment is finalized."
            ),
            continue_label="Verify documents →",
            continue_href="/college-admin/students/student-document-verification",
        )

    ay_options = [
        StudentAdminDashboardFilterOption(value=y.year_code, label=y.label or y.year_code) for y in years
    ]
    if not ay_options and selected_ay:
        ay_options = [StudentAdminDashboardFilterOption(value=selected_ay, label=selected_ay)]

    programme_options = [
        StudentAdminDashboardFilterOption(value="", label="All programmes"),
        *[
            StudentAdminDashboardFilterOption(value=p.programme_code, label=p.name or p.programme_code)
            for p in sorted(programmes, key=lambda x: x.name or x.programme_code)
        ],
    ]
    study_year_options = [
        StudentAdminDashboardFilterOption(value="", label="All years"),
        *[StudentAdminDashboardFilterOption(value=str(n), label=f"Year {n}") for n in range(1, 5)],
    ]

    page_subtitle = (
        f"Admissions, enrollment, documents and student status for {selected_ay.replace('-', '–')}"
        if selected_ay
        else "Admissions, enrollment, documents and student status"
    )

    work_queue = [
        StudentAdminWorkQueueItem(
            key="document_verification",
            title="Document verification",
            subtitle="Students",
            count=documents_pending,
            href="/college-admin/students/student-document-verification",
            action_label="Open →",
            icon_slug="file-check",
        ),
        StudentAdminWorkQueueItem(
            key="section_allocation",
            title="Section allocation",
            subtitle="Students",
            count=unassigned_sections,
            href="/college-admin/students/batch-section-allocation",
            action_label="Open →",
            icon_slug="layout-grid",
        ),
        StudentAdminWorkQueueItem(
            key="transfer_requests",
            title="Transfer requests",
            subtitle="Pending",
            count=transfer_total,
            href="/college-admin/students/student-transfer-management",
            action_label="Open →",
            icon_slug="arrow-right-left",
        ),
        StudentAdminWorkQueueItem(
            key="id_cards",
            title="ID cards to print",
            subtitle="Students",
            count=id_cards_pending,
            href="/college-admin/students/student-id-card-management",
            action_label="Open →",
            icon_slug="id-card",
        ),
    ]

    status_items = [
        StudentAdminStatusItem(status_key="active", status_label="Active", student_count=active_count),
        StudentAdminStatusItem(status_key="on_leave", status_label="On academic leave", student_count=on_leave),
        StudentAdminStatusItem(status_key="detained", status_label="Detained / year back", student_count=detained),
        StudentAdminStatusItem(status_key="discontinued", status_label="Discontinued", student_count=discontinued),
    ]

    kpis = [
        UserDashboardKpi(
            key="enrolled_students",
            label="Enrolled students",
            value=f"{total_enrolled:,}",
            hint_line=enrolled_hint,
            hint_tone=enrolled_hint_tone,
        ),
        UserDashboardKpi(
            key="admissions_year",
            label=f"Admissions {_display_academic_year(selected_ay, year_by_code)}" if selected_ay else "Admissions",
            value=f"{admissions_count:,}",
            hint_line=admissions_hint,
            hint_tone="neutral",
        ),
        UserDashboardKpi(
            key="documents_pending",
            label="Documents pending",
            value=f"{documents_pending:,}",
            hint_line=f"Verification overdue for {verification_overdue}" if verification_overdue else "All documents verified",
            hint_tone="warning" if documents_pending else "success",
        ),
        UserDashboardKpi(
            key="status_changes_month",
            label="Status changes this month",
            value=f"{status_changes:,}",
            hint_line="Transfers, withdrawals, leave",
            hint_tone="neutral",
        ),
    ]

    current_chart_label = (
        f"{_display_academic_year(selected_ay, year_by_code)} admissions"
        if selected_ay
        else "Current year admissions"
    )
    prev_chart_label = (
        f"{_display_academic_year(prev_ay, year_by_code)} admissions"
        if prev_ay
        else "Previous year admissions"
    )

    return StudentAdministrationDashboardPageRead(
        page_title="Student Administration Dashboard",
        page_subtitle=page_subtitle,
        export_label="Export",
        new_admission_label="New admission",
        new_admission_href="/college-admin/students/new-student-registration",
        academic_year_filter_label="Academic year",
        programme_filter_label="Programme",
        study_year_filter_label="Study year",
        scope_indicator_label="College scope",
        updated_at_label=_fmt_time_label(now),
        academic_year_options=ay_options,
        programme_options=programme_options,
        study_year_options=study_year_options,
        selected_academic_year=selected_ay,
        selected_programme_code=programme_code or "",
        selected_study_year=str(study_year) if study_year is not None else "",
        kpis=kpis,
        document_alert=document_alert,
        admissions_chart_title="Admissions by week",
        admissions_chart_current_label=current_chart_label,
        admissions_chart_previous_label=prev_chart_label,
        admissions_weekly_series=weekly_series,
        recent_admissions_title="Recent admissions",
        recent_admissions_headers=["Student", "Programme", "Quota", "Admitted", "Documents"],
        recent_admissions_rows=recent_rows,
        recent_admissions_footer_label=f"{admissions_count:,} admissions this year",
        recent_admissions_view_all_href="/college-admin/students/student-admission",
        recent_admissions_view_all_label="View all →",
        enrollment_by_year_title="Enrollment by year",
        enrollment_year_bars=enrollment_bars,
        work_queue_title="Work queue",
        work_queue_items=work_queue,
        student_status_title="Student status",
        student_status_items=status_items,
        footer_disclaimer="Live institutional data · Student admissions and records · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )