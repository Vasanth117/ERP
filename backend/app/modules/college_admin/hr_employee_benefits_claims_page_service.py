"""HR employee benefits & claims (CA 11.11)."""

from __future__ import annotations

import math
from datetime import datetime
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.college_admin.hr_benefits_performance_shared import HR_BENEFITS_PERFORMANCE_SUB_NAV
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    HrBenefitClaimTableRow,
    HrEmployeeBenefitsClaimsPageRead,
    PoliciesPagination,
    UserDashboardKpi,
)
from app.modules.hr.benefits_models import EmployeeBenefitClaim, EmployeeBenefitEnrollment, HrBenefitProgram
from app.modules.hr.enums import HrBenefitClaimStatus, HrBenefitEnrollmentStatus, HrBenefitProgramStatus

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 4
_TABLE_HEADERS = ["Employee", "Benefit", "Category", "Amount", "Submitted", "Status"]


def _fmt_snapshot(now: datetime) -> str:
    return now.astimezone(_IST).strftime("Snapshot · %d %b %Y, %H:%M IST")


def _claim_status_label(status: HrBenefitClaimStatus) -> tuple[str, str]:
    if status in {HrBenefitClaimStatus.AWAITING_REVIEW, HrBenefitClaimStatus.UNDER_REVIEW}:
        return "Pending", "warning"
    if status in {HrBenefitClaimStatus.APPROVED, HrBenefitClaimStatus.PARTIALLY_APPROVED, HrBenefitClaimStatus.AWAITING_PAYMENT}:
        return "Approved", "success"
    if status == HrBenefitClaimStatus.PAID:
        return "Paid", "success"
    if status == HrBenefitClaimStatus.REJECTED:
        return "Rejected", "error"
    if status == HrBenefitClaimStatus.PAYMENT_FAILED:
        return "Payment failed", "error"
    return status.value.replace("_", " ").title(), "muted"


async def get_hr_employee_benefits_claims_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> HrEmployeeBenefitsClaimsPageRead:
    authorize(scope, Permission.HR_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    programs = await HrBenefitProgram.find(Eq(HrBenefitProgram.tenant_id, tenant_id)).to_list()
    active_programs = sum(1 for p in programs if p.status == HrBenefitProgramStatus.ACTIVE)

    enrollments = await EmployeeBenefitEnrollment.find(Eq(EmployeeBenefitEnrollment.tenant_id, tenant_id)).to_list()
    enrolled = len({e.employee_user_id for e in enrollments if e.status == HrBenefitEnrollmentStatus.ACTIVE})

    claims = await EmployeeBenefitClaim.find(Eq(EmployeeBenefitClaim.tenant_id, tenant_id)).sort("-created_at").to_list()
    awaiting = sum(1 for c in claims if c.status in {HrBenefitClaimStatus.AWAITING_REVIEW, HrBenefitClaimStatus.UNDER_REVIEW})
    paid = sum(1 for c in claims if c.status == HrBenefitClaimStatus.PAID)

    program_by_id = {p.id: p for p in programs}
    user_ids = {c.employee_user_id for c in claims}
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_by_id = {u.id: u for u in users}

    claim_rows: list[HrBenefitClaimTableRow] = []
    for claim in claims:
        user = user_by_id.get(claim.employee_user_id)
        program = program_by_id.get(claim.benefit_program_id)
        status_label, status_tone = _claim_status_label(claim.status)
        submitted = claim.submitted_at or claim.created_at
        claim_rows.append(
            HrBenefitClaimTableRow(
                claim_id=str(claim.id),
                employee_name=user.full_name if user and user.full_name else "—",
                benefit_label=program.name if program else "—",
                category_label=claim.claim_category.replace("_", " ").title(),
                amount_label=f"₹{claim.requested_amount}",
                submitted_label=submitted.astimezone(_IST).strftime("%d %b %Y"),
                status_label=status_label,
                status_tone=status_tone,
                review_href=f"/college-admin/hr/employee-benefits-claims?claim_id={claim.id}",
            ),
        )

    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    total = len(claim_rows)
    total_pages = math.ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    visible = claim_rows[start : start + page_size]
    showing_end = min(total, start + len(visible)) if total else 0

    employee_count = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).count()

    kpis = [
        UserDashboardKpi(
            key="active_programs",
            label="Active programs",
            value=f"{active_programs:,}",
            hint_line=f"{len(programs):,} total",
            hint_tone="neutral",
        ),
        UserDashboardKpi(
            key="enrolled",
            label="Enrolled employees",
            value=f"{enrolled:,}",
            hint_line=f"of {employee_count:,}" if employee_count else "employees",
            hint_tone="info",
        ),
        UserDashboardKpi(
            key="claims_pending",
            label="Claims awaiting review",
            value=f"{awaiting:,}",
            hint_line="Needs action" if awaiting else "Clear",
            hint_tone="warning" if awaiting else "success",
        ),
        UserDashboardKpi(
            key="paid_claims",
            label="Paid claims",
            value=f"{paid:,}",
            hint_line="All time",
            hint_tone="success" if paid else "neutral",
        ),
    ]

    return HrEmployeeBenefitsClaimsPageRead(
        page_title="Employee Benefits & Claims",
        page_subtitle="Benefit programs and reimbursement claims",
        new_program_label="New benefit program",
        new_program_href="/college-admin/hr/hr-settings-policies",
        sub_nav=HR_BENEFITS_PERFORMANCE_SUB_NAV,
        kpis=kpis,
        claims_section_title="Claims",
        table_headers=_TABLE_HEADERS,
        claim_rows=visible,
        showing_label=f"Showing {showing_end} of {total}",
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages) if total_pages else [],
            has_previous=page > 1,
            has_next=page < total_pages if total_pages else False,
        ),
        footer_disclaimer="Live institutional data · Benefits and claims · All times IST",
        footer_snapshot_label=_fmt_snapshot(now),
        generated_at=now,
    )