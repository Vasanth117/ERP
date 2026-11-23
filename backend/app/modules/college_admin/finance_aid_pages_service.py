"""Scholarship, concession and refund management pages (CA 10)."""

from __future__ import annotations

import math
from collections import defaultdict
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.accounts_finance.phase5_enums import ConcessionApplicationStatus, ScholarshipProgramStatus
from app.modules.accounts_finance.phase5_models import (
    FeeConcessionCategory,
    FeeConcessionPolicy,
    StudentFeeConcessionApplication,
    StudentFeeConcessionAward,
    StudentScholarshipAward,
)
from app.modules.accounts_finance.phase7_enums import RefundWorkflowStatus
from app.modules.accounts_finance.phase7_models import StudentRefundRequest
from app.modules.auth.models import User
from app.modules.college_admin.finance_aid_page_shared import (
    aid_sub_nav,
    format_count,
    format_inr,
    format_inr_compact,
    page_numbers,
    refund_display_id,
    short_date,
    showing_slice,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    ConcessionWaiverManagementPageRead,
    FinanceConcessionTableRow,
    FinanceRefundTableRow,
    FinanceScholarshipTableRow,
    PoliciesPagination,
    RefundManagementPageRead,
    ScholarshipManagementPageRead,
    UserDashboardKpi,
)
from app.modules.finance.finance_enums import RefundStatus, ScholarshipApplicationStatus
from app.modules.finance.finance_models import OfficialScholarshipApplication, RefundRecord, ScholarshipProgram

_PAGE_SIZE = 10


def _pagination(total: int, page: int, page_size: int) -> tuple[PoliciesPagination, int]:
    total_pages = math.ceil(total / page_size) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * page_size
    return (
        PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            page_numbers=page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        start,
    )


def _program_category(program: ScholarshipProgram) -> str:
    source = (program.funding_source or program.scholarship_type or "").lower()
    if "gov" in source or "central" in source or "state" in source:
        return "Government"
    if source:
        return source.replace("_", " ").title()
    return "Institutional"


def _program_status(program: ScholarshipProgram) -> tuple[str, str]:
    status = (program.program_status or "").lower()
    if program.applications_open or status in {"open", ScholarshipProgramStatus.OPEN.value}:
        return "Open", "success"
    if status in {"closed", ScholarshipProgramStatus.CLOSED.value, ScholarshipProgramStatus.EXPIRED.value}:
        return "Closed", "muted"
    if program.applications_open:
        return "Open", "success"
    return "Draft", "muted"


def _concession_status(status: ConcessionApplicationStatus) -> tuple[str, str]:
    if status in (ConcessionApplicationStatus.SUBMITTED, ConcessionApplicationStatus.UNDER_REVIEW, ConcessionApplicationStatus.DRAFT):
        return "Pending", "warning"
    if status in (ConcessionApplicationStatus.APPROVED, ConcessionApplicationStatus.ACTIVE):
        return "Approved", "success"
    if status == ConcessionApplicationStatus.REJECTED:
        return "Rejected", "error"
    return status.value.replace("_", " ").title(), "muted"


def _refund_stage(
    record: RefundRecord,
    workflow: StudentRefundRequest | None,
) -> tuple[str, str]:
    if record.status == RefundStatus.PROCESSED:
        return "Completed", "success"
    if workflow is not None:
        if workflow.status in (RefundWorkflowStatus.PROCESSING, RefundWorkflowStatus.AWAITING_PROCESSING):
            return "Initiated", "info"
        if workflow.status == RefundWorkflowStatus.APPROVED:
            return "Approved", "info"
        if workflow.status in (
            RefundWorkflowStatus.SUBMITTED,
            RefundWorkflowStatus.PENDING_APPROVAL,
            RefundWorkflowStatus.UNDER_REVIEW,
        ):
            return "Requested", "warning"
        if workflow.status == RefundWorkflowStatus.SUCCESSFUL:
            return "Completed", "success"
    if record.status == RefundStatus.APPROVED:
        return "Approved", "info"
    if record.status == RefundStatus.REQUESTED:
        return "Requested", "warning"
    if record.status == RefundStatus.REJECTED:
        return "Rejected", "error"
    return "Requested", "warning"


async def get_scholarship_management_page(scope: AccessScope, *, page: int = 1) -> ScholarshipManagementPageRead:
    authorize(scope, Permission.FINANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    programs = await ScholarshipProgram.find(Eq(ScholarshipProgram.tenant_id, tenant_id)).sort("-updated_at").to_list()
    applications = await OfficialScholarshipApplication.find(
        Eq(OfficialScholarshipApplication.tenant_id, tenant_id),
    ).to_list()
    awards = await StudentScholarshipAward.find(Eq(StudentScholarshipAward.tenant_id, tenant_id)).to_list()

    open_programs = sum(1 for p in programs if p.applications_open or (p.program_status or "").lower() == "open")
    pending_verification = sum(
        1
        for a in applications
        if a.status in (ScholarshipApplicationStatus.SUBMITTED, ScholarshipApplicationStatus.IN_REVIEW)
    )
    awarded_total = sum(a.approved_amount for a in awards)
    awarded_students = len({a.student_user_id for a in awards if a.approved_amount > 0})

    apps_by_program: dict[str, list[OfficialScholarshipApplication]] = defaultdict(list)
    for app in applications:
        apps_by_program[app.programme_id].append(app)
    awards_by_program: dict[str, list[StudentScholarshipAward]] = defaultdict(list)
    for award in awards:
        awards_by_program[award.programme_id].append(award)

    kpis = [
        UserDashboardKpi(
            key="programmes",
            label="Programmes",
            value=str(len(programs)),
            hint_line=f"{open_programs} open",
            hint_tone="blue",
        ),
        UserDashboardKpi(
            key="applications",
            label="Applications",
            value=format_count(len(applications)),
            hint_line="",
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="pending_verification",
            label="Pending verification",
            value=str(pending_verification),
            hint_line="",
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="awarded",
            label="Awarded",
            value=format_inr_compact(awarded_total),
            hint_line=f"{format_count(awarded_students)} students",
            hint_tone="green",
        ),
    ]

    total = len(programs)
    pagination, start = _pagination(total, page, _PAGE_SIZE)
    page_programs = programs[start : start + _PAGE_SIZE]

    table_rows: list[FinanceScholarshipTableRow] = []
    for program in page_programs:
        prog_apps = apps_by_program.get(program.programme_id, [])
        prog_awards = awards_by_program.get(program.programme_id, [])
        students = len({a.student_user_id for a in prog_apps} | {a.student_user_id for a in prog_awards})
        awarded_amt = sum(a.approved_amount for a in prog_awards)
        applied_amt = sum(a.requested_award_amount or 0 for a in prog_apps)
        status_label, status_tone = _program_status(program)
        table_rows.append(
            FinanceScholarshipTableRow(
                scheme_label=program.title,
                category_label=_program_category(program),
                students_label=format_count(students),
                awarded_label=format_inr_compact(awarded_amt),
                applied_label=format_inr_compact(applied_amt),
                status_label=status_label,
                status_tone=status_tone,
                detail_href="/college-admin/finance/scholarship-management",
            )
        )

    return ScholarshipManagementPageRead(
        page_title="Scholarship Management",
        page_subtitle="Programmes, applications and awards",
        new_programme_label="New programme",
        new_programme_href="/college-admin/finance/scholarship-management?create=1",
        kpis=kpis,
        sub_nav=aid_sub_nav("scholarships"),
        scholarships_section_title="Scholarships",
        table_headers=["Scheme", "Category", "Students", "Awarded", "Applied", "Status"],
        scholarship_rows=table_rows,
        list_count_label=showing_slice(len(page_programs), total),
        showing_label=showing_slice(min(start + len(page_programs), total), total),
        pagination=pagination,
        generated_at=now,
    )


async def get_concession_waiver_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
) -> ConcessionWaiverManagementPageRead:
    authorize(scope, Permission.FINANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    applications = await StudentFeeConcessionApplication.find(
        Eq(StudentFeeConcessionApplication.tenant_id, tenant_id),
    ).sort("-created_at").to_list()
    awards = await StudentFeeConcessionAward.find(Eq(StudentFeeConcessionAward.tenant_id, tenant_id)).to_list()
    policies = await FeeConcessionPolicy.find(Eq(FeeConcessionPolicy.tenant_id, tenant_id)).to_list()
    categories = await FeeConcessionCategory.find(Eq(FeeConcessionCategory.tenant_id, tenant_id)).to_list()
    policy_by_id = {p.policy_id: p for p in policies}
    category_by_id = {c.category_id: c for c in categories}

    pending = [
        a
        for a in applications
        if a.status in (ConcessionApplicationStatus.SUBMITTED, ConcessionApplicationStatus.UNDER_REVIEW, ConcessionApplicationStatus.DRAFT)
    ]
    approved_apps = [a for a in applications if a.status in (ConcessionApplicationStatus.APPROVED, ConcessionApplicationStatus.ACTIVE)]
    rejected = [a for a in applications if a.status == ConcessionApplicationStatus.REJECTED]
    approved_amount = sum(a.approved_amount for a in awards)
    if approved_amount <= 0:
        approved_amount = sum(a.requested_amount or 0 for a in approved_apps)

    kpis = [
        UserDashboardKpi(key="requests", label="Requests", value=str(len(applications)), hint_line="", hint_tone="muted"),
        UserDashboardKpi(key="pending", label="Pending", value=str(len(pending)), hint_line="", hint_tone="muted"),
        UserDashboardKpi(
            key="approved",
            label="Approved",
            value=str(len(approved_apps)),
            hint_line=format_inr_compact(approved_amount),
            hint_tone="green",
        ),
        UserDashboardKpi(key="rejected", label="Rejected", value=str(len(rejected)), hint_line="", hint_tone="muted"),
    ]

    total = len(applications)
    pagination, start = _pagination(total, page, _PAGE_SIZE)
    page_apps = applications[start : start + _PAGE_SIZE]

    user_ids = {a.student_user_id for a in page_apps}
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_names = {u.id: (u.full_name or "—").strip() or "—" for u in users}

    def category_label(app: StudentFeeConcessionApplication) -> str:
        policy = policy_by_id.get(app.policy_id)
        if app.category_id and app.category_id in category_by_id:
            return category_by_id[app.category_id].name
        if policy:
            if policy.category_id and policy.category_id in category_by_id:
                return category_by_id[policy.category_id].name
            return policy.name
        return "General"

    def approver_label(app: StudentFeeConcessionApplication) -> str:
        policy = policy_by_id.get(app.policy_id)
        if policy and policy.approval_hierarchy:
            return policy.approval_hierarchy[-1].replace("_", " ").title()
        status_label, _ = _concession_status(app.status)
        if status_label == "Approved":
            return "Principal"
        return "Finance Manager"

    table_rows: list[FinanceConcessionTableRow] = []
    for app in page_apps:
        status_label, status_tone = _concession_status(app.status)
        policy = policy_by_id.get(app.policy_id)
        amount = app.requested_amount or (policy.fixed_amount if policy and policy.fixed_amount else 0) or 0
        table_rows.append(
            FinanceConcessionTableRow(
                student_name=user_names.get(app.student_user_id, "—"),
                category_label=category_label(app),
                requested_label=format_inr(amount),
                date_label=short_date(app.created_at),
                approver_label=approver_label(app),
                status_label=status_label,
                status_tone=status_tone,
                detail_href="/college-admin/finance/fee-concession-waiver-management",
            )
        )

    return ConcessionWaiverManagementPageRead(
        page_title="Fee Concession & Waiver Management",
        page_subtitle="Concession requests and approvals",
        new_request_label="New request",
        new_request_href="/college-admin/finance/fee-concession-waiver-management?create=1",
        kpis=kpis,
        sub_nav=aid_sub_nav("concessions"),
        requests_section_title="Concession requests",
        table_headers=["Student", "Category", "Requested", "Date", "Approver", "Status"],
        concession_rows=table_rows,
        list_count_label=showing_slice(len(page_apps), total),
        showing_label=showing_slice(min(start + len(page_apps), total), total),
        pagination=pagination,
        generated_at=now,
    )


async def get_refund_management_page(scope: AccessScope, *, page: int = 1) -> RefundManagementPageRead:
    authorize(scope, Permission.FINANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    records = await RefundRecord.find(Eq(RefundRecord.tenant_id, tenant_id)).sort("-created_at").to_list()
    workflows = await StudentRefundRequest.find(Eq(StudentRefundRequest.tenant_id, tenant_id)).to_list()
    workflow_by_ref = {w.refund_request_id: w for w in workflows}
    workflow_by_tx: dict[str, StudentRefundRequest] = {w.transaction_id: w for w in workflows if w.transaction_id}

    stage_counts = {"requested": 0, "approved": 0, "initiated": 0, "completed": 0}
    stage_amounts = {"requested": 0.0, "completed": 0.0}
    for record in records:
        workflow = None
        if record.refund_request_id:
            workflow = workflow_by_ref.get(record.refund_request_id)
        if workflow is None and record.transaction_id:
            workflow = workflow_by_tx.get(record.transaction_id)
        stage, _ = _refund_stage(record, workflow)
        key = stage.lower()
        if key == "requested":
            stage_counts["requested"] += 1
            stage_amounts["requested"] += record.amount
        elif key == "approved":
            stage_counts["approved"] += 1
        elif key == "initiated":
            stage_counts["initiated"] += 1
        elif key == "completed":
            stage_counts["completed"] += 1
            stage_amounts["completed"] += record.amount

    kpis = [
        UserDashboardKpi(
            key="requested",
            label="Requested",
            value=str(stage_counts["requested"]),
            hint_line=format_inr_compact(stage_amounts["requested"]),
            hint_tone="amber",
        ),
        UserDashboardKpi(key="approved", label="Approved", value=str(stage_counts["approved"]), hint_line="", hint_tone="muted"),
        UserDashboardKpi(key="initiated", label="Initiated", value=str(stage_counts["initiated"]), hint_line="", hint_tone="muted"),
        UserDashboardKpi(
            key="completed",
            label="Completed",
            value=str(stage_counts["completed"]),
            hint_line=format_inr_compact(stage_amounts["completed"]),
            hint_tone="green",
        ),
    ]

    total = len(records)
    pagination, start = _pagination(total, page, _PAGE_SIZE)
    page_records = records[start : start + _PAGE_SIZE]

    user_ids = {r.student_user_id for r in page_records}
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_names = {u.id: (u.full_name or "—").strip() or "—" for u in users}

    table_rows: list[FinanceRefundTableRow] = []
    for record in page_records:
        workflow = None
        if record.refund_request_id:
            workflow = workflow_by_ref.get(record.refund_request_id)
        if workflow is None and record.transaction_id:
            workflow = workflow_by_tx.get(record.transaction_id)
        stage_label, stage_tone = _refund_stage(record, workflow)
        original_tx = record.transaction_id or (workflow.transaction_id if workflow else "—")
        table_rows.append(
            FinanceRefundTableRow(
                refund_label=refund_display_id(record.refund_id),
                student_name=user_names.get(record.student_user_id, "—"),
                original_transaction_label=original_tx,
                amount_label=format_inr(record.amount),
                requested_label=short_date(record.created_at),
                stage_label=stage_label,
                stage_tone=stage_tone,
                detail_href="/college-admin/finance/refund-management",
            )
        )

    return RefundManagementPageRead(
        page_title="Refund Management",
        page_subtitle="Requested, approved, initiated and completed",
        new_request_label="New request",
        new_request_href="/college-admin/finance/refund-management?create=1",
        kpis=kpis,
        sub_nav=aid_sub_nav("refunds"),
        refunds_section_title="Refunds",
        table_headers=["Refund", "Student", "Original", "Amount", "Requested", "Stage"],
        refund_rows=table_rows,
        list_count_label=showing_slice(len(page_records), total),
        showing_label=showing_slice(min(start + len(page_records), total), total),
        pagination=pagination,
        generated_at=now,
    )