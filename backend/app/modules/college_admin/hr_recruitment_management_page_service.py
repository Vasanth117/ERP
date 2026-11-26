"""HR recruitment management (CA 11.03)."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, GTE, In, LTE

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.college_admin.hr_admin_models import RecruitmentRecord, RecruitmentStatus
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    HrRecruitmentManagementPageRead,
    HrRecruitmentSubNavItem,
    HrRecruitmentVacancyRow,
    PoliciesPagination,
    UserDashboardKpi,
)
from app.modules.hr.enums import (
    HrApplicationPipelineStage,
    HrEmploymentOfferStatus,
    HrInterviewStatus,
    HrJobOpeningStatus,
)
from app.modules.hr.recruitment_models import (
    HrEmploymentOffer,
    HrInterviewSession,
    HrJobApplication,
    HrJobOpening,
)

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 4
_CLOSING_WINDOW_DAYS = 7
_INTERVIEW_STAGES = frozenset(
    {
        HrApplicationPipelineStage.INTERVIEW_SCHEDULED,
        HrApplicationPipelineStage.INTERVIEW_COMPLETED,
        HrApplicationPipelineStage.FINAL_EVALUATION,
    },
)
_TABLE_HEADERS = ["Position", "Department", "Openings", "Applicants", "Closes", "Status"]

_SUB_NAV = [
    HrRecruitmentSubNavItem(
        key="recruitment",
        label="Recruitment management",
        href="/college-admin/hr/recruitment-management",
    ),
    HrRecruitmentSubNavItem(
        key="onboarding",
        label="Employee onboarding",
        href="/college-admin/hr/employee-onboarding",
    ),
]


def _fmt_snapshot(now: datetime) -> str:
    local = now.astimezone(_IST)
    return f"Snapshot · {local.strftime('%d %b %Y, %H:%M IST')}"


def _closes_label(deadline: datetime | None) -> str:
    if deadline is None:
        return "—"
    return deadline.astimezone(_IST).strftime("%d %b")


def _vacancy_status(
    *,
    has_interviews: bool,
    closing_soon: bool,
    status: HrJobOpeningStatus,
) -> tuple[str, str]:
    if has_interviews:
        return "Interviews", "info"
    if closing_soon and status == HrJobOpeningStatus.PUBLISHED:
        return "Closing", "warning"
    if status == HrJobOpeningStatus.PUBLISHED:
        return "Open", "success"
    if status == HrJobOpeningStatus.PAUSED:
        return "Paused", "muted"
    return status.value.replace("_", " ").title(), "muted"


async def get_hr_recruitment_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> HrRecruitmentManagementPageRead:
    authorize(scope, Permission.HR_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.astimezone(_IST).date()
    horizon = now + timedelta(days=_CLOSING_WINDOW_DAYS)

    openings = await HrJobOpening.find(
        Eq(HrJobOpening.tenant_id, tenant_id),
        In(
            HrJobOpening.status,
            [
                HrJobOpeningStatus.PUBLISHED,
                HrJobOpeningStatus.PAUSED,
                HrJobOpeningStatus.DRAFT,
            ],
        ),
    ).sort("-updated_at").to_list()

    departments = await InstitutionDepartment.find(Eq(InstitutionDepartment.tenant_id, tenant_id)).to_list()
    dept_by_id = {d.id: d for d in departments}

    applications = await HrJobApplication.find(Eq(HrJobApplication.tenant_id, tenant_id)).to_list()
    apps_by_opening: dict[PydanticObjectId, int] = defaultdict(int)
    interview_openings: set[PydanticObjectId] = set()
    for app in applications:
        apps_by_opening[app.job_opening_id] += 1
        if app.stage in _INTERVIEW_STAGES:
            interview_openings.add(app.job_opening_id)

    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=7)
    week_start_dt = datetime.combine(week_start, datetime.min.time(), tzinfo=_IST)
    week_end_dt = datetime.combine(week_end, datetime.min.time(), tzinfo=_IST)

    interviews_week = await HrInterviewSession.find(
        Eq(HrInterviewSession.tenant_id, tenant_id),
        In(HrInterviewSession.status, [HrInterviewStatus.SCHEDULED, HrInterviewStatus.COMPLETED]),
        GTE(HrInterviewSession.scheduled_at, week_start_dt),
        LTE(HrInterviewSession.scheduled_at, week_end_dt),
    ).count()

    offers_made = await HrEmploymentOffer.find(
        Eq(HrEmploymentOffer.tenant_id, tenant_id),
        In(
            HrEmploymentOffer.status,
            [
                HrEmploymentOfferStatus.ISSUED,
                HrEmploymentOfferStatus.ACCEPTED,
                HrEmploymentOfferStatus.APPROVED,
            ],
        ),
    ).count()

    open_vacancies = sum(max(0, o.vacancies - o.filled_count) for o in openings if o.status == HrJobOpeningStatus.PUBLISHED)
    legacy_open = await RecruitmentRecord.find(
        Eq(RecruitmentRecord.tenant_id, tenant_id),
        Eq(RecruitmentRecord.status, RecruitmentStatus.OPEN),
    ).count()
    open_vacancies = max(open_vacancies, legacy_open)
    total_applicants = len(applications)

    rows: list[HrRecruitmentVacancyRow] = []
    for opening in openings:
        dept = dept_by_id.get(opening.department_id)
        closing_soon = bool(
            opening.application_deadline
            and opening.status == HrJobOpeningStatus.PUBLISHED
            and opening.application_deadline <= horizon
        )
        status_label, status_tone = _vacancy_status(
            has_interviews=opening.id in interview_openings,
            closing_soon=closing_soon,
            status=opening.status,
        )
        rows.append(
            HrRecruitmentVacancyRow(
                opening_id=str(opening.id),
                position_label=opening.job_title,
                department_label=dept.name if dept else "—",
                openings_count=max(0, opening.vacancies - opening.filled_count),
                applicants_count=apps_by_opening.get(opening.id, 0),
                closes_label=_closes_label(opening.application_deadline),
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/hr/recruitment-management?opening_id={opening.id}",
            )
        )

    if not rows and legacy_open:
        legacy_rows = await RecruitmentRecord.find(
            Eq(RecruitmentRecord.tenant_id, tenant_id),
            Eq(RecruitmentRecord.status, RecruitmentStatus.OPEN),
        ).to_list()
        for record in legacy_rows:
            dept = dept_by_id.get(record.department_id) if record.department_id else None
            rows.append(
                HrRecruitmentVacancyRow(
                    opening_id=record.requisition_id,
                    position_label=record.role_title,
                    department_label=dept.name if dept else "—",
                    openings_count=1,
                    applicants_count=record.applicant_count,
                    closes_label="—",
                    status_label="Open",
                    status_tone="success",
                    detail_href=f"/college-admin/hr/recruitment-management?requisition_id={record.requisition_id}",
                )
            )

    rows.sort(key=lambda r: r.position_label.lower())
    total = len(rows)
    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    total_pages = math.ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    paged = rows[start : start + page_size]
    showing_end = min(total, start + len(paged)) if total else 0

    kpis = [
        UserDashboardKpi(
            key="open_vacancies",
            label="Open vacancies",
            value=f"{open_vacancies:,}",
            hint_line="Published roles",
            hint_tone="neutral",
        ),
        UserDashboardKpi(
            key="applicants",
            label="Applicants",
            value=f"{total_applicants:,}",
            hint_line="Total applications",
            hint_tone="neutral",
        ),
        UserDashboardKpi(
            key="interviews_week",
            label="Interviews this week",
            value=f"{interviews_week:,}",
            hint_line="Scheduled or completed",
            hint_tone="neutral",
        ),
        UserDashboardKpi(
            key="offers_made",
            label="Offers made",
            value=f"{offers_made:,}",
            hint_line="Issued or accepted",
            hint_tone="neutral",
        ),
    ]

    return HrRecruitmentManagementPageRead(
        page_title="Recruitment Management",
        page_subtitle="Vacancies, applicants and interviews",
        new_vacancy_label="New vacancy",
        new_vacancy_href="/college-admin/hr/recruitment-management?create=1",
        kpis=kpis,
        sub_nav=_SUB_NAV,
        vacancies_section_title="Vacancies",
        table_headers=_TABLE_HEADERS,
        vacancy_rows=paged,
        showing_label=f"{showing_end} of {total:,}" if total else "0 of 0",
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        footer_disclaimer="Live institutional data · HR recruitment records · All times IST",
        footer_snapshot_label=_fmt_snapshot(now),
        generated_at=now,
    )