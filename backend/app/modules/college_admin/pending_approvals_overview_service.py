"""College admin dashboard — pending approvals overview."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.attendance.enums import AttendanceCorrectionStatus
from app.modules.attendance.models import AttendanceCorrectionRequest
from app.modules.auth.models import User
from app.modules.college_admin.enums import DashboardDateRange, PendingApprovalCategory
from app.modules.college_admin.finance_admin_models import FinancialApprovalRecord, RefundRequest
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.models import InstitutionSettings
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    PendingApprovalByModuleItem,
    PendingApprovalEscalationItem,
    PendingApprovalOverviewFilters,
    PendingApprovalOverviewKpiRead,
    PendingApprovalOverviewRead,
    PendingApprovalModuleFilterOption,
    PendingApprovalQueueRow,
    PendingApprovalRecentDecisionItem,
    PendingApprovalRequesterFilterOption,
)
from app.modules.college_admin.workflow_admin_models import (
    ApprovalTaskStatus,
    InstitutionApprovalHistory,
    InstitutionApprovalTask,
    InstitutionWorkflowEscalation,
    InstitutionWorkflowInstance,
    WorkflowModule,
)
from app.modules.examinations.exam_cell_timetable_enums import ExamScheduleApprovalDecision
from app.modules.examinations.exam_cell_timetable_models import ExamScheduleApproval, ExamTimetable
from app.modules.finance.finance_enums import RefundStatus

_reader = OperationalDataReader()

_MODULE_LABELS: dict[str, str] = {
    WorkflowModule.ADMISSIONS.value: "Admissions",
    WorkflowModule.LEAVE.value: "HR & leave",
    WorkflowModule.ATTENDANCE.value: "Attendance",
    WorkflowModule.EXAMINATION.value: "Examinations",
    WorkflowModule.FINANCE.value: "Finance",
    WorkflowModule.PROCUREMENT.value: "Operations & others",
    WorkflowModule.STUDENT_SERVICES.value: "Academics",
    WorkflowModule.HOSTEL.value: "Hostel",
    WorkflowModule.LIBRARY.value: "Library",
    WorkflowModule.CUSTOM.value: "Operations & others",
}

_CATEGORY_MODULE: dict[PendingApprovalCategory, str] = {
    PendingApprovalCategory.ATTENDANCE: "Attendance",
    PendingApprovalCategory.ASSESSMENT: "Examinations",
    PendingApprovalCategory.LEAVE: "HR & leave",
    PendingApprovalCategory.STUDENT_REQUEST: "Academics",
    PendingApprovalCategory.ENROLLMENT: "Academics",
    PendingApprovalCategory.PROFILE_CORRECTION: "Academics",
    PendingApprovalCategory.HOSTEL: "Hostel",
    PendingApprovalCategory.SCHOLARSHIP: "Finance",
    PendingApprovalCategory.OTHER: "Operations & others",
}

_CATEGORY_REQUESTER: dict[PendingApprovalCategory, str] = {
    PendingApprovalCategory.ATTENDANCE: "Attendance Cell",
    PendingApprovalCategory.ASSESSMENT: "Examination Cell",
    PendingApprovalCategory.LEAVE: "HR Office",
    PendingApprovalCategory.ENROLLMENT: "Academics Office",
    PendingApprovalCategory.PROFILE_CORRECTION: "Student Services",
    PendingApprovalCategory.HOSTEL: "Hostel Admin",
    PendingApprovalCategory.STUDENT_REQUEST: "Student Services",
    PendingApprovalCategory.SCHOLARSHIP: "Finance Office",
    PendingApprovalCategory.OTHER: "Institution",
}


def _date_window(anchor: datetime, range_key: DashboardDateRange | None) -> tuple[datetime | None, datetime | None]:
    if not range_key or range_key == DashboardDateRange.SEMESTER:
        return None, None
    start = anchor.replace(hour=0, minute=0, second=0, microsecond=0)
    if range_key == DashboardDateRange.TODAY:
        return start, start + timedelta(days=1)
    if range_key == DashboardDateRange.WEEK:
        return start - timedelta(days=anchor.weekday()), start + timedelta(days=7 - anchor.weekday())
    if range_key == DashboardDateRange.MONTH:
        month_start = start.replace(day=1)
        if month_start.month == 12:
            end = month_start.replace(year=month_start.year + 1, month=1)
        else:
            end = month_start.replace(month=month_start.month + 1)
        return month_start, end
    return None, None


def _fmt_submitted(dt: datetime) -> str:
    local = dt.astimezone(timezone.utc)
    return f"{local.day} {local.strftime('%b')}"


def _sla(
    *,
    submitted_at: datetime,
    deadline_at: datetime | None,
    now: datetime,
    default_days: int,
) -> tuple[str, str, int | None]:
    due = deadline_at or (submitted_at + timedelta(days=default_days))
    if due.tzinfo is None:
        due = due.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    if due < now:
        overdue_days = max(0, (now.date() - due.date()).days)
        return "overdue", "Overdue", overdue_days
    days_left = (due.date() - now.date()).days
    if days_left == 0:
        return "due_today", "Due today", 0
    if days_left == 1:
        return "due_soon", "1 day left", 1
    due_label = f"Due {due.day} {due.strftime('%b')}"
    return "due_soon", due_label if days_left > 1 else "1 day left", days_left


def _request_code(ref: str) -> str:
    clean = ref.replace("-", "").upper()[-8:]
    return f"APR-{clean[:4]}"


async def get_pending_approvals_overview(
    scope: AccessScope,
    *,
    date_range: DashboardDateRange | None = None,
    module_key: str | None = None,
    requester_id: str | None = None,
) -> PendingApprovalOverviewRead:
    authorize(scope, Permission.COLLEGE_DASHBOARD_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    inst_settings = await InstitutionSettings.find_one(Eq(InstitutionSettings.tenant_id, tenant_id))
    sla_days = int((inst_settings.settings or {}).get("approval_sla_days", 7)) if inst_settings else 7
    overdue_sla_days = int((inst_settings.settings or {}).get("approval_overdue_days", 3)) if inst_settings else 3

    window_start, window_end = _date_window(now, date_range)

    rows: list[PendingApprovalQueueRow] = []
    module_counts: dict[str, int] = defaultdict(int)

    tasks = await InstitutionApprovalTask.find(
        Eq(InstitutionApprovalTask.tenant_id, tenant_id),
        Eq(InstitutionApprovalTask.status, ApprovalTaskStatus.PENDING),
    ).to_list()
    instance_ids = {t.instance_id for t in tasks}
    all_instances = await InstitutionWorkflowInstance.find(Eq(InstitutionWorkflowInstance.tenant_id, tenant_id)).to_list()
    instance_by_id = {i.instance_id: i for i in all_instances if i.instance_id in instance_ids}

    requester_ids = {i.requester_id for i in instance_by_id.values()}
    user_names: dict[PydanticObjectId, str] = {}
    if requester_ids:
        for uid in requester_ids:
            user = await User.get(uid)
            if user:
                user_names[uid] = user.full_name or user.email or str(uid)

    for task in tasks:
        instance = instance_by_id.get(task.instance_id)
        if instance is None:
            continue
        module = instance.module.value if hasattr(instance.module, "value") else str(instance.module)
        module_label = _MODULE_LABELS.get(module, module.replace("_", " ").title())
        if module_key and module != module_key and module_key.lower() not in module_label.lower():
            continue
        requester = user_names.get(instance.requester_id, "—")
        if requester_id and str(instance.requester_id) != requester_id:
            continue
        submitted = task.created_at
        if window_start and submitted < window_start:
            continue
        if window_end and submitted >= window_end:
            continue
        deadline = task.deadline_at or instance.deadline_at
        sla_key, sla_label, overdue_days = _sla(
            submitted_at=submitted,
            deadline_at=deadline,
            now=now,
            default_days=sla_days,
        )
        title = instance.context.get("title") or f"{instance.resource_type.replace('_', ' ').title()}"
        rows.append(
            PendingApprovalQueueRow(
                reference_id=task.task_id,
                request_code=_request_code(task.task_id),
                title=title,
                module_key=module,
                module_label=module_label,
                requested_by_label=requester,
                requester_user_id=str(instance.requester_id),
                submitted_at=submitted,
                submitted_label=_fmt_submitted(submitted),
                sla_key=sla_key,
                sla_label=sla_label,
                overdue_days=overdue_days,
                review_resource_type="approval_task",
                review_resource_id=task.task_id,
            )
        )
        module_counts[module_label] += 1

    operational = await _reader.pending_approvals(tenant_id, limit=100)
    for item in operational:
        module_label = _CATEGORY_MODULE.get(item.category, "Operations & others")
        mod_key = item.category.value
        if module_key and module_key not in (mod_key, module_label.lower().replace(" ", "_")):
            continue
        if window_start and item.submitted_at < window_start:
            continue
        if window_end and item.submitted_at >= window_end:
            continue
        sla_key, sla_label, overdue_days = _sla(
            submitted_at=item.submitted_at,
            deadline_at=None,
            now=now,
            default_days=sla_days,
        )
        rows.append(
            PendingApprovalQueueRow(
                reference_id=item.reference_id,
                request_code=_request_code(item.reference_id),
                title=item.title,
                module_key=mod_key,
                module_label=module_label,
                requested_by_label=_CATEGORY_REQUESTER.get(item.category, "Institution"),
                requester_user_id=None,
                submitted_at=item.submitted_at,
                submitted_label=_fmt_submitted(item.submitted_at),
                sla_key=sla_key,
                sla_label=sla_label,
                overdue_days=overdue_days,
                review_resource_type=item.category.value,
                review_resource_id=item.reference_id,
            )
        )
        module_counts[module_label] += 1

    timetable_ids: dict = {}
    for approval in await ExamScheduleApproval.find(
        Eq(ExamScheduleApproval.tenant_id, tenant_id),
        Eq(ExamScheduleApproval.decision, ExamScheduleApprovalDecision.PENDING),
    ).to_list():
        tt = timetable_ids.get(approval.timetable_id)
        if tt is None:
            tt = await ExamTimetable.get(approval.timetable_id)
            timetable_ids[approval.timetable_id] = tt
        title = tt.title if tt else "Exam timetable approval"
        submitted = approval.created_at
        if window_start and submitted < window_start:
            continue
        sla_key, sla_label, overdue_days = _sla(submitted_at=submitted, deadline_at=None, now=now, default_days=sla_days)
        module_label = "Examinations"
        if module_key and module_key not in ("examination", "examinations"):
            continue
        rows.append(
            PendingApprovalQueueRow(
                reference_id=approval.approval_id,
                request_code=_request_code(approval.approval_id),
                title=title,
                module_key="examination",
                module_label=module_label,
                requested_by_label="Examination Cell",
                requester_user_id=None,
                submitted_at=submitted,
                submitted_label=_fmt_submitted(submitted),
                sla_key=sla_key,
                sla_label=sla_label,
                overdue_days=overdue_days,
                review_resource_type="exam_timetable",
                review_resource_id=approval.approval_id,
            )
        )
        module_counts[module_label] += 1

    for refund in await RefundRequest.find(
        Eq(RefundRequest.tenant_id, tenant_id),
        Eq(RefundRequest.status, RefundStatus.REQUESTED),
    ).to_list():
        if module_key and module_key not in ("finance",):
            continue
        submitted = refund.created_at
        if window_start and submitted < window_start:
            continue
        sla_key, sla_label, overdue_days = _sla(submitted_at=submitted, deadline_at=None, now=now, default_days=sla_days)
        rows.append(
            PendingApprovalQueueRow(
                reference_id=refund.refund_id,
                request_code=_request_code(refund.refund_id),
                title=f"Refund request — ₹{refund.amount:,.0f}",
                module_key="finance",
                module_label="Finance",
                requested_by_label="Accounts Office",
                requester_user_id=str(refund.student_user_id),
                submitted_at=submitted,
                submitted_label=_fmt_submitted(submitted),
                sla_key=sla_key,
                sla_label=sla_label,
                overdue_days=overdue_days,
                review_resource_type="refund",
                review_resource_id=refund.refund_id,
            )
        )
        module_counts["Finance"] += 1

    for correction in await AttendanceCorrectionRequest.find(
        Eq(AttendanceCorrectionRequest.tenant_id, tenant_id),
        Eq(AttendanceCorrectionRequest.status, AttendanceCorrectionStatus.PENDING),
    ).to_list():
        if module_key and module_key not in ("attendance",):
            continue
        submitted = correction.created_at
        if window_start and submitted < window_start:
            continue
        sla_key, sla_label, overdue_days = _sla(submitted_at=submitted, deadline_at=None, now=now, default_days=sla_days)
        rows.append(
            PendingApprovalQueueRow(
                reference_id=str(correction.id),
                request_code=_request_code(str(correction.id)),
                title="Attendance correction",
                module_key="attendance",
                module_label="Attendance",
                requested_by_label="Faculty",
                requester_user_id=str(correction.faculty_user_id),
                submitted_at=submitted,
                submitted_label=_fmt_submitted(submitted),
                sla_key=sla_key,
                sla_label=sla_label,
                overdue_days=overdue_days,
                review_resource_type="attendance_correction",
                review_resource_id=str(correction.id),
            )
        )
        module_counts["Attendance"] += 1

    def sort_key(r: PendingApprovalQueueRow) -> tuple:
        overdue = 0 if r.sla_key == "overdue" else 1
        days = r.overdue_days if r.sla_key == "overdue" else (r.overdue_days or 999)
        return (overdue, days, -r.submitted_at.timestamp())

    rows.sort(key=sort_key)
    total = len(rows)
    table_limit = 7
    visible_rows = rows[:table_limit]

    unique_modules = {r.module_label for r in rows}
    overdue_count = sum(
        1 for r in rows if r.sla_key == "overdue" and (r.overdue_days or 0) >= overdue_sla_days
    )
    escalated_tasks = await InstitutionApprovalTask.find(
        Eq(InstitutionApprovalTask.tenant_id, tenant_id),
        Eq(InstitutionApprovalTask.status, ApprovalTaskStatus.ESCALATED),
    ).count()
    escalations = await InstitutionWorkflowEscalation.find(Eq(InstitutionWorkflowEscalation.tenant_id, tenant_id)).to_list()
    escalated_count = escalated_tasks + len(escalations)

    week_start = now - timedelta(days=now.weekday())
    approved_tasks = await InstitutionApprovalTask.find(
        Eq(InstitutionApprovalTask.tenant_id, tenant_id),
        Eq(InstitutionApprovalTask.status, ApprovalTaskStatus.APPROVED),
    ).to_list()
    approved_week = [t for t in approved_tasks if t.completed_at and t.completed_at >= week_start]
    financial_approved = await FinancialApprovalRecord.find(Eq(FinancialApprovalRecord.tenant_id, tenant_id)).to_list()
    financial_week = [r for r in financial_approved if r.decision == "approved" and r.created_at >= week_start]

    turnarounds: list[float] = []
    for task in approved_week:
        if not task.completed_at:
            continue
        hours = (task.completed_at - task.created_at).total_seconds() / 3600
        turnarounds.append(hours / 24)
    avg_turnaround = round(sum(turnarounds) / len(turnarounds), 1) if turnarounds else None

    by_module = [
        PendingApprovalByModuleItem(
            module_key=label.lower().replace(" ", "_").replace("&", "and"),
            module_label=label,
            count=count,
        )
        for label, count in sorted(module_counts.items(), key=lambda x: -x[1])
    ]
    max_count = max((m.count for m in by_module), default=1)

    escalation_items: list[PendingApprovalEscalationItem] = []
    for esc in sorted(escalations, key=lambda e: e.created_at, reverse=True)[:5]:
        instance = instance_by_id.get(esc.instance_id)
        if instance is None:
            instance = await InstitutionWorkflowInstance.find_one(
                Eq(InstitutionWorkflowInstance.tenant_id, tenant_id),
                Eq(InstitutionWorkflowInstance.instance_id, esc.instance_id),
            )
        title = instance.context.get("title") if instance and instance.context else esc.reason
        age_days = (now - esc.created_at).days
        priority = "high" if age_days >= 7 else "medium"
        escalation_items.append(
            PendingApprovalEscalationItem(
                escalation_id=esc.escalation_id,
                title=title or esc.reason,
                escalated_by_label=esc.escalated_to_permission or "Registrar",
                age_days=age_days,
                priority_key=priority,
                priority_label="High" if priority == "high" else "Medium",
            )
        )

    history = await InstitutionApprovalHistory.find(Eq(InstitutionApprovalHistory.tenant_id, tenant_id)).sort("-created_at").limit(20).to_list()
    recent: list[PendingApprovalRecentDecisionItem] = []
    for event in history:
        decision = "approved" if "approv" in event.event.lower() or "approv" in event.summary.lower() else "rejected" if "reject" in event.event.lower() else "info"
        if decision == "info":
            continue
        recent.append(
            PendingApprovalRecentDecisionItem(
                event_id=str(event.id),
                title=event.summary,
                decision_key=decision,
                decision_label="Approved" if decision == "approved" else "Rejected",
                decided_at=event.created_at,
                detail=event.metadata.get("note") if event.metadata else None,
            )
        )
        if len(recent) >= 5:
            break

    requester_filter: list[PendingApprovalRequesterFilterOption] = []
    seen_requesters: set[str] = set()
    for row in rows:
        if not row.requester_user_id or row.requester_user_id in seen_requesters:
            continue
        seen_requesters.add(row.requester_user_id)
        try:
            oid = PydanticObjectId(row.requester_user_id)
            label = user_names.get(oid, row.requested_by_label)
        except Exception:
            label = row.requested_by_label
        requester_filter.append(PendingApprovalRequesterFilterOption(user_id=row.requester_user_id, label=label))

    module_options: dict[str, str] = {}
    for row in rows:
        module_options[row.module_key] = row.module_label
    module_filter = [
        PendingApprovalModuleFilterOption(module_key=key, module_label=label)
        for key, label in sorted(module_options.items(), key=lambda item: item[1])
    ]

    return PendingApprovalOverviewRead(
        filters=PendingApprovalOverviewFilters(
            date_range=date_range,
            module_key=module_key,
            requester_id=requester_id,
        ),
        kpis=PendingApprovalOverviewKpiRead(
            awaiting_action=total,
            modules_with_pending=len(unique_modules),
            overdue_count=overdue_count,
            overdue_sla_days=overdue_sla_days,
            approved_this_week=len(approved_week) + len(financial_week),
            avg_turnaround_days=avg_turnaround,
            escalated_to_college_admin=escalated_count,
        ),
        queue_rows=visible_rows,
        queue_total=total,
        queue_limit=table_limit,
        pending_by_module=by_module,
        pending_by_module_max=max_count,
        escalations=escalation_items,
        recently_decided=recent,
        module_filter_options=module_filter,
        requester_filter_options=requester_filter,
        generated_at=now,
    )