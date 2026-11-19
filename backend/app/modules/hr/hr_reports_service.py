"""HR analytics, reports, exports and scheduling."""

from datetime import date, timedelta
from uuid import uuid4

from beanie.odm.operators.find.comparison import Eq

from app.authorization.policy import authorize
from app.authorization.permissions import Permission
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.department_admin.csv_safe import encode_csv_base64, rows_to_csv
from app.modules.hr.benefits_models import EmployeeBenefitClaim
from app.modules.hr.dashboard_filters import build_hr_dashboard_context
from app.modules.hr.dashboard_repository import HrDashboardRepository
from app.modules.hr.enums import (
    HrBenefitClaimStatus,
    HrDashboardDateRange,
    HrPayrollRunStatus,
    HrPerformanceReviewStatus,
    HrTrainingEnrollmentStatus,
    LeaveRequestStatus,
)
from app.modules.hr.models import LeaveRequest
from app.modules.hr.payroll_models import HrPayrollRun
from app.modules.hr.performance_models import EmployeePerformanceReview
from app.modules.hr.policy import authorize_hr_reports_export, authorize_hr_reports_manage, authorize_hr_reports_read, require_hr_tenant_scope
from app.modules.hr.recruitment_models import HrJobApplication
from app.modules.hr.training_models import HrTrainingEnrollment
from app.modules.hr.hr_reports_catalog import catalog_for_scope, catalog_item
from app.modules.hr.hr_reports_models import HrReportExecutionHistory, HrSavedReport, HrScheduledReport
from app.modules.hr.hr_reports_repository import HrReportsRepository
from app.modules.hr.hr_reports_schemas import (
    HrAnalyticsDashboard,
    ReportCatalogItemRead,
    ReportDataRead,
    ReportExportRead,
    ReportExportRequest,
    ReportRunRequest,
    SavedReportRead,
    SavedReportUpsert,
    ScheduledReportRead,
    ScheduledReportUpsert,
)

_repo = HrReportsRepository()
_dash_repo = HrDashboardRepository()


def _authorize_report(scope: AccessScope, report_key: str) -> None:
    item = catalog_item(report_key)
    if item is None:
        raise AppError(code="NOT_FOUND", message="Unknown report", status_code=404)
    if Permission.HR_REPORTS_MANAGE not in scope.effective_permissions and Permission.HR_ADMIN_MANAGE not in scope.effective_permissions:
        authorize(scope, Permission(item.required_permission))


async def analytics_dashboard(scope: AccessScope) -> HrAnalyticsDashboard:
    authorize_hr_reports_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    dash = HrAnalyticsDashboard()
    employees = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    dash.workforce_size = len(employees)
    dash.active_employees = sum(1 for e in employees if e.employment_status == FacultyEmploymentStatus.ACTIVE)
    leaves = await LeaveRequest.find(Eq(LeaveRequest.tenant_id, tenant_id)).to_list()
    dash.pending_leaves = sum(1 for l in leaves if l.status in {LeaveRequestStatus.PENDING_MANAGER, LeaveRequestStatus.PENDING_HR})
    claims = await EmployeeBenefitClaim.find(Eq(EmployeeBenefitClaim.tenant_id, tenant_id)).to_list()
    dash.pending_claims = sum(1 for c in claims if c.status == HrBenefitClaimStatus.AWAITING_REVIEW)
    dash.open_payroll_runs = await HrPayrollRun.find(
        Eq(HrPayrollRun.tenant_id, tenant_id),
        Eq(HrPayrollRun.status, HrPayrollRunStatus.DRAFT),
    ).count()
    reviews = await EmployeePerformanceReview.find(Eq(EmployeePerformanceReview.tenant_id, tenant_id)).to_list()
    dash.pending_reviews = sum(1 for r in reviews if r.status != HrPerformanceReviewStatus.FINALIZED)
    enrollments = await HrTrainingEnrollment.find(Eq(HrTrainingEnrollment.tenant_id, tenant_id)).to_list()
    dash.training_in_progress = sum(1 for e in enrollments if e.status == HrTrainingEnrollmentStatus.CONFIRMED)
    dash.recruitment_applications = await HrJobApplication.find(Eq(HrJobApplication.tenant_id, tenant_id)).count()

    this_month = date.today().replace(day=1)
    last_month_end = this_month - timedelta(days=1)
    ctx_now = build_hr_dashboard_context(
        tenant_id,
        department_id=None,
        campus_id=None,
        anchor_date=date.today(),
        date_range=HrDashboardDateRange.MONTH,
        date_from=None,
        date_to=None,
    )
    ctx_prev = build_hr_dashboard_context(
        tenant_id,
        department_id=None,
        campus_id=None,
        anchor_date=last_month_end,
        date_range=HrDashboardDateRange.MONTH,
        date_from=None,
        date_to=None,
    )
    emp_now = await _dash_repo.employee_overview(ctx_now)
    emp_prev = await _dash_repo.employee_overview(ctx_prev)
    dash.comparisons = {
        "workforce_mom": {
            "current_total": emp_now.total,
            "previous_total": emp_prev.total,
            "note": "month-over-month employee totals (scoped filters not applied)",
        }
    }
    return dash


async def list_report_catalog(scope: AccessScope) -> list[ReportCatalogItemRead]:
    authorize_hr_reports_read(scope)
    items = catalog_for_scope(scope.effective_permissions)
    return [
        ReportCatalogItemRead(
            report_key=i.report_key,
            title=i.title,
            category=i.category,
            supported_formats=list(i.supported_formats),
        )
        for i in items
    ]


async def run_report(scope: AccessScope, payload: ReportRunRequest) -> ReportDataRead:
    _authorize_report(scope, payload.report_key)
    tenant_id = require_hr_tenant_scope(scope)
    rows, totals = await _repo.build(tenant_id, payload.report_key, payload.filters)
    allowed_fields = payload.filters.get("selected_fields")
    if allowed_fields:
        rows = [{k: v for k, v in row.items() if k in allowed_fields} for row in rows]
    return ReportDataRead(
        report_key=payload.report_key,
        row_count=len(rows),
        totals=totals,
        rows=rows,
        generated_at=utcnow(),
    )


async def export_report(scope: AccessScope, payload: ReportExportRequest) -> ReportExportRead:
    authorize_hr_reports_export(scope)
    _authorize_report(scope, payload.report_key)
    tenant_id = require_hr_tenant_scope(scope)
    if payload.idempotency_key:
        existing = await HrReportExecutionHistory.find_one(
            Eq(HrReportExecutionHistory.tenant_id, tenant_id),
            Eq(HrReportExecutionHistory.filters, {"idempotency_key": payload.idempotency_key}),
        )
        if existing:
            return ReportExportRead.from_doc(existing)
    data = await run_report(scope, ReportRunRequest(report_key=payload.report_key, filters=payload.filters))
    b64 = None
    if payload.export_format.value == "csv" and data.rows:
        fields = list(data.rows[0].keys())
        b64 = encode_csv_base64(rows_to_csv(data.rows, fields))
    elif payload.export_format.value != "csv":
        raise AppError(code="VALIDATION_ERROR", message="Only CSV export is supported in this phase", status_code=422)
    doc = HrReportExecutionHistory(
        tenant_id=tenant_id,
        report_key=payload.report_key,
        export_format=payload.export_format,
        status="completed" if b64 else "empty",
        row_count=data.row_count,
        filters=payload.filters,
        file_content_base64=b64,
        actor_id=scope.user_id,
        completed_at=utcnow(),
    )
    await doc.insert()
    return ReportExportRead.from_doc(doc)


async def save_report(scope: AccessScope, payload: SavedReportUpsert) -> SavedReportRead:
    authorize_hr_reports_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    _authorize_report(scope, payload.report_key)
    row = HrSavedReport(
        tenant_id=tenant_id,
        report_key=payload.report_key,
        name=payload.name,
        selected_fields=payload.selected_fields,
        filters=payload.filters,
        group_by=payload.group_by,
        sort_by=payload.sort_by,
        owner_id=scope.user_id,
    )
    await row.insert()
    return SavedReportRead.from_doc(row)


async def list_saved_reports(scope: AccessScope) -> list[SavedReportRead]:
    authorize_hr_reports_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rows = await HrSavedReport.find(Eq(HrSavedReport.tenant_id, tenant_id), Eq(HrSavedReport.owner_id, scope.user_id)).to_list()
    return [SavedReportRead.from_doc(r) for r in rows]


async def schedule_report(scope: AccessScope, payload: ScheduledReportUpsert) -> ScheduledReportRead:
    authorize_hr_reports_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    _authorize_report(scope, payload.report_key)
    recipients = [to_object_id(x, "recipient_user_id") for x in payload.recipient_user_ids]
    row = HrScheduledReport(
        tenant_id=tenant_id,
        schedule_code=payload.schedule_code,
        report_key=payload.report_key,
        saved_report_id=to_object_id(payload.saved_report_id, "saved_report_id") if payload.saved_report_id else None,
        frequency=payload.frequency,
        filters=payload.filters,
        export_format=payload.export_format,
        recipient_user_ids=recipients,
        delivery_channel=payload.delivery_channel,
        next_run_at=utcnow() + timedelta(days=1),
        actor_id=scope.user_id,
    )
    await row.insert()
    return ScheduledReportRead.from_doc(row)


async def execute_scheduled_report(scope: AccessScope, schedule_id: str) -> ReportExportRead:
    authorize_hr_reports_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    sid = to_object_id(schedule_id, "schedule_id")
    sched = await HrScheduledReport.get(sid)
    if sched is None or sched.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Schedule not found", status_code=404)
    export = await export_report(
        scope,
        ReportExportRequest(report_key=sched.report_key, export_format=sched.export_format, filters=sched.filters),
    )
    sched.last_run_at = utcnow()
    sched.last_status = export.status
    sched.updated_at = utcnow()
    await sched.save()
    hist = await HrReportExecutionHistory.get(to_object_id(export.execution_id, "execution_id"))
    if hist:
        hist.scheduled_report_id = sched.id
        await hist.save()
    return export


async def get_export_download(scope: AccessScope, execution_id: str) -> dict:
    authorize_hr_reports_export(scope)
    tenant_id = require_hr_tenant_scope(scope)
    eid = to_object_id(execution_id, "execution_id")
    doc = await HrReportExecutionHistory.get(eid)
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Export not found", status_code=404)
    if not doc.file_content_base64:
        raise AppError(code="NOT_FOUND", message="No export file", status_code=404)
    return {"report_key": doc.report_key, "format": doc.export_format.value, "content_base64": doc.file_content_base64}