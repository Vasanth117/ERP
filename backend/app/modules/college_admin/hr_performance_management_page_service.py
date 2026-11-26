"""HR performance management dashboard (CA 11.12)."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.college_admin.hr_benefits_performance_shared import HR_BENEFITS_PERFORMANCE_SUB_NAV
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    HrPerformanceManagementPageRead,
    HrPerformanceProgressRow,
    UserDashboardKpi,
)
from app.modules.hr.enums import HrPerformanceCycleStatus, HrPerformanceReviewStatus, HrTrainingEnrollmentStatus
from app.modules.hr.performance_models import EmployeePerformanceReview, HrPerformanceCycle
from app.modules.hr.training_models import HrTrainingEnrollment

_IST = ZoneInfo("Asia/Kolkata")
_ACTIVE_EMPLOYMENT = frozenset(
    {
        FacultyEmploymentStatus.ACTIVE,
        FacultyEmploymentStatus.CONFIRMED,
        FacultyEmploymentStatus.PROBATION,
        FacultyEmploymentStatus.AWAITING_CONFIRMATION,
        FacultyEmploymentStatus.ON_LEAVE,
        FacultyEmploymentStatus.NOTICE_PERIOD,
    },
)


def _fmt_snapshot(now: datetime) -> str:
    return now.astimezone(_IST).strftime("Snapshot · %d %b %Y, %H:%M IST")


def _cycle_subtitle(cycle: HrPerformanceCycle | None) -> str:
    if cycle is None:
        today = utcnow().astimezone(_IST).date()
        end_year = today.year + 1 if today.month >= 4 else today.year
        start_year = end_year - 1
        return f"Appraisal cycle {start_year}-{str(end_year)[-2:]}"
    if cycle.title:
        return cycle.title
    return f"Appraisal cycle {cycle.start_date.year}-{str(cycle.end_date.year)[-2:]}"


async def _resolve_cycle(tenant_id) -> HrPerformanceCycle | None:
    active = await HrPerformanceCycle.find_one(
        Eq(HrPerformanceCycle.tenant_id, tenant_id),
        Eq(HrPerformanceCycle.status, HrPerformanceCycleStatus.ACTIVE),
    )
    if active:
        return active
    rows = await HrPerformanceCycle.find(Eq(HrPerformanceCycle.tenant_id, tenant_id)).sort("-start_date").to_list()
    return rows[0] if rows else None


def _progress_pct(done: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((done / total) * 100, 1)


async def get_hr_performance_management_page(scope: AccessScope) -> HrPerformanceManagementPageRead:
    authorize(scope, Permission.HR_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    cycle = await _resolve_cycle(tenant_id)
    reviews = (
        await EmployeePerformanceReview.find(
            Eq(EmployeePerformanceReview.tenant_id, tenant_id),
            Eq(EmployeePerformanceReview.cycle_id, cycle.id),
        ).to_list()
        if cycle
        else []
    )

    if not reviews and cycle is None:
        employee_count = await EmployeeRecord.find(
            Eq(EmployeeRecord.tenant_id, tenant_id),
            In(EmployeeRecord.employment_status, list(_ACTIVE_EMPLOYMENT)),
        ).count()
        total = employee_count
    else:
        total = len(reviews) if reviews else await EmployeeRecord.find(
            Eq(EmployeeRecord.tenant_id, tenant_id),
            In(EmployeeRecord.employment_status, list(_ACTIVE_EMPLOYMENT)),
        ).count()

    self_done = sum(
        1
        for r in reviews
        if r.status
        not in {HrPerformanceReviewStatus.NOT_STARTED, HrPerformanceReviewStatus.SELF_ASSESSMENT}
    )
    manager_done = sum(
        1
        for r in reviews
        if r.status in {HrPerformanceReviewStatus.HR_REVIEW, HrPerformanceReviewStatus.FINALIZED}
    )
    calibration_done = sum(1 for r in reviews if r.status == HrPerformanceReviewStatus.FINALIZED)
    calibration_pending = sum(1 for r in reviews if r.status == HrPerformanceReviewStatus.HR_REVIEW)

    training_enrolled = await HrTrainingEnrollment.find(
        Eq(HrTrainingEnrollment.tenant_id, tenant_id),
        In(
            HrTrainingEnrollment.status,
            [
                HrTrainingEnrollmentStatus.CONFIRMED,
                HrTrainingEnrollmentStatus.COMPLETED,
                HrTrainingEnrollmentStatus.NOMINATED,
                HrTrainingEnrollmentStatus.PENDING_APPROVAL,
            ],
        ),
    ).count()

    can_open = cycle is None or cycle.status != HrPerformanceCycleStatus.ACTIVE
    blocked: str | None = None
    if cycle and cycle.status == HrPerformanceCycleStatus.ACTIVE:
        blocked = "Appraisal cycle is already open."

    kpis = [
        UserDashboardKpi(
            key="self_reviews",
            label="Self reviews done",
            value=f"{self_done:,}",
            hint_line=f"of {total:,}",
            hint_tone="success" if self_done and total else "neutral",
        ),
        UserDashboardKpi(
            key="manager_reviews",
            label="Manager reviews done",
            value=f"{manager_done:,}",
            hint_line="Submitted to HR" if manager_done else "Pending",
            hint_tone="neutral",
        ),
        UserDashboardKpi(
            key="calibration_pending",
            label="Calibration pending",
            value=f"{calibration_pending:,}",
            hint_line="HR review",
            hint_tone="warning" if calibration_pending else "neutral",
        ),
        UserDashboardKpi(
            key="training_enrolled",
            label="Training enrolled",
            value=f"{training_enrolled:,}",
            hint_line="Active enrollments",
            hint_tone="info" if training_enrolled else "neutral",
        ),
    ]

    progress_rows = [
        HrPerformanceProgressRow(
            key="self_review",
            label="Self review",
            completed_count=self_done,
            total_count=total,
            progress_pct=_progress_pct(self_done, total),
            tone="info",
        ),
        HrPerformanceProgressRow(
            key="manager_review",
            label="Manager review",
            completed_count=manager_done,
            total_count=total,
            progress_pct=_progress_pct(manager_done, total),
            tone="info",
        ),
        HrPerformanceProgressRow(
            key="calibration",
            label="Calibration",
            completed_count=calibration_done,
            total_count=total,
            progress_pct=_progress_pct(calibration_done, total),
            tone="warning",
        ),
    ]

    return HrPerformanceManagementPageRead(
        page_title="Performance Management",
        page_subtitle=_cycle_subtitle(cycle),
        open_cycle_label="Open cycle",
        can_open_cycle=can_open,
        open_cycle_blocked_message=blocked,
        selected_cycle_id=str(cycle.id) if cycle else None,
        sub_nav=HR_BENEFITS_PERFORMANCE_SUB_NAV,
        kpis=kpis,
        progress_section_title="Appraisal progress",
        progress_rows=progress_rows,
        footer_disclaimer="Live institutional data · Performance management · All times IST",
        footer_snapshot_label=_fmt_snapshot(now),
        generated_at=now,
    )