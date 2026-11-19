"""Department Admin — reports and analytics (aggregates over existing modules)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.ids import to_object_id
from app.common.schemas import Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.department_admin.audit_helpers import record_department_audit
from app.modules.auth.models import User
from app.modules.department_admin.assessment_monitoring_service import marks_submission_overview
from app.modules.department_admin.attendance_oversight_service import attendance_shortages, list_correction_requests
from app.modules.department_admin.csv_safe import encode_csv_base64, rows_to_csv
from app.modules.department_admin.dashboard_service import (
    get_attendance_dashboard_summary,
    get_student_dashboard_stats,
    get_timetable_dashboard_summary,
)
from app.modules.department_admin.examination_monitoring_service import examination_readiness, list_examinations
from app.modules.department_admin.faculty_management_service import list_faculty_directory
from app.modules.department_admin.models import DepartmentReportJob, DepartmentReportJobStatus
from app.modules.department_admin.performance_monitoring_service import (
    performance_batches,
    performance_overview,
    performance_programmes,
    performance_pass_fail,
)
from app.modules.department_admin.performance_schemas import PerformanceFilters
from app.modules.department_admin.phase5_schemas import AssessmentMonitoringFilters
from app.modules.department_admin.phase7_schemas import RequestFilters
from app.modules.department_admin.phase8_schemas import (
    ReportDataRead,
    ReportDownloadRead,
    ReportFilters,
    ReportGenerateBody,
    ReportJobRead,
    ReportsOverviewRead,
)
from app.modules.department_admin.policy import resolve_authorized_department
from app.modules.department_admin.reports_catalog import REPORT_CATALOG
from app.modules.department_admin.requests_workflow_service import requests_summary
from app.modules.department_admin.resource_service import resource_utilization
from app.modules.department_admin.schemas import DepartmentDashboardFilters
from app.modules.department_admin.student_administration_service import list_students
from app.modules.department_admin.phase3_schemas import StudentDirectoryFilters
from app.modules.messaging.outbox_models import DomainOutboxEvent, OutboxEventStatus

RETENTION_HOURS = 72
LARGE_ROW_THRESHOLD = 500


def _catalog_item(report_type: str):
    for item in REPORT_CATALOG:
        if item.report_type == report_type:
            return item
    return None


def _require_catalog_permission(scope: AccessScope, report_type: str) -> None:
    item = _catalog_item(report_type)
    if item is None:
        raise AppError(code="NOT_FOUND", message="Unknown report type", status_code=404)
    perm = Permission(item.required_permission)
    authorize(scope, perm)


async def _validate_report_filters(
    filters: ReportFilters,
    *,
    tenant_id: PydanticObjectId,
    central_id: PydanticObjectId,
    institution,
) -> None:
    programmes = {c.upper() for c in institution.programme_codes}
    if filters.programme_code and filters.programme_code.upper() not in programmes:
        raise AppError(code="FORBIDDEN", message="Programme outside department", status_code=403)
    if filters.faculty_user_id:
        from app.modules.department_admin.department_scope import assert_faculty_visible_to_department

        await assert_faculty_visible_to_department(tenant_id, central_id, to_object_id(filters.faculty_user_id, "faculty_user_id"))


def _perf_filters(filters: ReportFilters) -> PerformanceFilters:
    return PerformanceFilters(
        academic_year_label=filters.academic_year_label,
        semester_label=filters.semester_label,
        programme_code=filters.programme_code,
        batch_label=filters.batch_label,
        section_code=filters.section_code,
        course_code=filters.course_code,
    )


def _assessment_filters(filters: ReportFilters) -> AssessmentMonitoringFilters:
    return AssessmentMonitoringFilters(
        academic_year_label=filters.academic_year_label,
        semester_label=filters.semester_label,
        programme_code=filters.programme_code,
        batch_label=filters.batch_label,
        section_code=filters.section_code,
        course_code=filters.course_code,
        faculty_user_id=filters.faculty_user_id,
        date_from=filters.date_from,
        date_to=filters.date_to,
    )


async def _build_report_data(scope: AccessScope, user: User, report_type: str, filters: ReportFilters) -> ReportDataRead:
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    await _validate_report_filters(filters, tenant_id=tenant_id, central_id=central_id, institution=institution)
    _require_catalog_permission(scope, report_type)
    now = utcnow()
    rows: list[dict] = []
    totals: dict = {}
    meta: dict = {"department_scoped": True, "academic_period": filters.academic_year_label}

    if report_type == "faculty_workload":
        page = await list_faculty_directory(scope, user, pagination=Pagination(limit=500, offset=0))
        for item in page.items:
            rows.append(
                {
                    "faculty_user_id": item.faculty_user_id,
                    "full_name": item.full_name,
                    "email": item.email,
                    "assignment_count": len(item.assigned_subjects),
                    "workload_total_hours": item.workload_total_hours,
                    "designation": item.designation,
                }
            )
        totals = {"faculty_listed": len(rows)}
    elif report_type == "student_enrollment":
        stats = await get_student_dashboard_stats(
            scope,
            user,
            filters=DepartmentDashboardFilters(
                academic_year_label=filters.academic_year_label,
                semester_label=filters.semester_label,
                programme_code=filters.programme_code,
                batch_label=filters.batch_label,
                section_code=filters.section_code,
            ),
        )
        totals = stats.model_dump(mode="json")
        prof = await performance_programmes(scope, user, filters=_perf_filters(filters))
        rows = [p.model_dump(mode="json") for p in prof]
    elif report_type == "attendance":
        overview = await get_attendance_dashboard_summary(scope, user)
        totals = overview.model_dump(mode="json")
        shortages = await attendance_shortages(scope, user)
        rows = [r.model_dump(mode="json") for r in shortages[:200]]
        corrections = await list_correction_requests(scope, user, pagination=Pagination(limit=50, offset=0))
        meta["pending_corrections"] = corrections.total
    elif report_type == "academic_performance":
        overview = await performance_overview(scope, user, filters=_perf_filters(filters))
        totals = overview.model_dump(mode="json")
        pf = await performance_pass_fail(scope, user, filters=_perf_filters(filters))
        rows = [pf.model_dump(mode="json")]
        batches = await performance_batches(scope, user, filters=_perf_filters(filters))
        rows.extend([b.model_dump(mode="json") for b in batches])
        meta["pass_fail_included"] = True
    elif report_type == "timetable":
        overview = await get_timetable_dashboard_summary(
            scope,
            user,
            anchor_date=filters.date_from.date() if filters.date_from else None,
        )
        totals = overview.model_dump(mode="json")
        meta["note"] = "Classroom utilization is advisory without a facility master."
    elif report_type == "examination_readiness":
        readiness = await examination_readiness(scope, user, filters=_assessment_filters(filters))
        totals = readiness.model_dump(mode="json")
        marks = await marks_submission_overview(scope, user, filters=_assessment_filters(filters))
        rows = [marks.model_dump(mode="json")]
        exams = await list_examinations(scope, user, filters=_assessment_filters(filters), pagination=Pagination(limit=100, offset=0))
        meta["examination_rows"] = exams.total
    elif report_type == "operations":
        req = await requests_summary(scope, user, filters=RequestFilters(date_from=filters.date_from, date_to=filters.date_to))
        util = await resource_utilization(scope, user)
        totals = {"requests": req.model_dump(mode="json"), "resources": util.model_dump(mode="json")}
        rows = [{"category": k, "count": v} for k, v in req.by_category.items()]
    else:
        raise AppError(code="NOT_FOUND", message="Unknown report type", status_code=404)

    return ReportDataRead(
        report_type=report_type,
        filters=filters,
        generated_at=now,
        row_count=len(rows),
        totals=totals,
        rows=rows,
        meta=meta,
    )


def list_report_catalog(scope: AccessScope) -> list:
    authorize(scope, Permission.DEPARTMENT_REPORTS_READ)
    visible = []
    for item in REPORT_CATALOG:
        if Permission(item.required_permission) in scope.effective_permissions:
            visible.append(item)
    return visible


async def reports_overview(scope: AccessScope, user: User) -> ReportsOverviewRead:
    authorize(scope, Permission.DEPARTMENT_REPORTS_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    recent = await DepartmentReportJob.find(
        {"tenant_id": tenant_id, "central_department_id": central_id}
    ).sort("-created_at").limit(20).to_list()
    pending = sum(1 for j in recent if j.status in {DepartmentReportJobStatus.PENDING, DepartmentReportJobStatus.PROCESSING})
    cats = sorted({c.category for c in REPORT_CATALOG})
    return ReportsOverviewRead(
        catalogue_count=len(REPORT_CATALOG),
        recent_jobs=len(recent),
        pending_jobs=pending,
        categories=cats,
        generated_at=utcnow(),
        advisory="Report values are computed from canonical collections at generation time.",
    )


async def get_report_snapshot(scope: AccessScope, user: User, report_type: str, filters: ReportFilters) -> ReportDataRead:
    authorize(scope, Permission.DEPARTMENT_REPORTS_READ)
    return await _build_report_data(scope, user, report_type, filters)


def _job_read(doc: DepartmentReportJob) -> ReportJobRead:
    return ReportJobRead(
        job_id=str(doc.id),
        report_type=doc.report_type,
        output_format=doc.output_format,
        status=doc.status,
        row_count=doc.row_count,
        filters=doc.filters,
        expires_at=doc.expires_at,
        created_at=doc.created_at,
        completed_at=doc.completed_at,
        error_message=doc.error_message,
        has_download=bool(doc.file_content_base64),
    )


async def generate_report(scope: AccessScope, user: User, body: ReportGenerateBody) -> ReportJobRead:
    authorize(scope, Permission.DEPARTMENT_REPORTS_GENERATE)
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    _require_catalog_permission(scope, body.report_type)
    if body.idempotency_key:
        existing = await DepartmentReportJob.find_one(
            Eq(DepartmentReportJob.tenant_id, tenant_id),
            Eq(DepartmentReportJob.idempotency_key, body.idempotency_key),
        )
        if existing and existing.central_department_id == central_id:
            return _job_read(existing)
    expires = utcnow() + timedelta(hours=RETENTION_HOURS)
    job = DepartmentReportJob(
        tenant_id=tenant_id,
        central_department_id=central_id,
        requested_by=user.id,
        report_type=body.report_type,
        filters=body.filters.model_dump(mode="json"),
        output_format=body.output_format,
        status=DepartmentReportJobStatus.PROCESSING,
        expires_at=expires,
        idempotency_key=body.idempotency_key,
    )
    await job.insert()
    try:
        data = await _build_report_data(scope, user, body.report_type, body.filters)
        job.row_count = data.row_count
        job.result_preview = {"totals": data.totals, "meta": data.meta}
        if body.output_format == "json":
            job.result_preview["rows"] = data.rows[:1000]
        elif body.output_format == "csv" and data.rows:
            fields = list(data.rows[0].keys())
            csv_text = rows_to_csv(data.rows, fields)
            job.file_content_base64 = encode_csv_base64(csv_text)
        job.status = DepartmentReportJobStatus.COMPLETED
        job.completed_at = utcnow()
        if data.row_count > LARGE_ROW_THRESHOLD and body.async_large:
            key = body.idempotency_key or f"dept_report:{job.id}"
            if not await DomainOutboxEvent.find_one(
                Eq(DomainOutboxEvent.tenant_id, tenant_id), Eq(DomainOutboxEvent.idempotency_key, key)
            ):
                await DomainOutboxEvent(
                    tenant_id=tenant_id,
                    event_type="department.report.generated",
                    aggregate_type="department_report_job",
                    aggregate_id=str(job.id),
                    payload={"job_id": str(job.id), "report_type": body.report_type},
                    idempotency_key=key,
                    status=OutboxEventStatus.PENDING,
                ).insert()
    except AppError:
        job.status = DepartmentReportJobStatus.FAILED
        raise
    except Exception as exc:
        job.status = DepartmentReportJobStatus.FAILED
        job.error_message = "Report generation failed"
        await job.save()
        raise AppError(code="INTERNAL_ERROR", message="Report generation failed", status_code=500) from exc
    await job.save()
    await record_department_audit(
        actor_id=user.id,
        action="department.report.generated",
        resource_type="department_report_job",
        resource_id=str(job.id),
        tenant_id=tenant_id,
        metadata={"report_type": body.report_type, "format": body.output_format},
        central_department_id=central_id,
    )
    return _job_read(job)


async def get_report_job(scope: AccessScope, user: User, job_id: str) -> ReportJobRead:
    authorize(scope, Permission.DEPARTMENT_REPORTS_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await DepartmentReportJob.get(to_object_id(job_id, "job_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Report job not found", status_code=404)
    if doc.expires_at and doc.expires_at < utcnow():
        doc.status = DepartmentReportJobStatus.EXPIRED
        await doc.save()
    return _job_read(doc)


async def download_report_job(scope: AccessScope, user: User, job_id: str) -> ReportDownloadRead:
    authorize(scope, Permission.DEPARTMENT_REPORTS_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await DepartmentReportJob.get(to_object_id(job_id, "job_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Report job not found", status_code=404)
    if doc.requested_by != user.id:
        authorize(scope, Permission.DEPARTMENT_REPORTS_GENERATE)
    if doc.expires_at and doc.expires_at < utcnow():
        raise AppError(code="FORBIDDEN", message="Report download expired", status_code=403)
    if not doc.file_content_base64:
        raise AppError(code="NOT_FOUND", message="No downloadable artifact for this job", status_code=404)
    await record_department_audit(
        actor_id=user.id,
        action="department.report.downloaded",
        resource_type="department_report_job",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    ext = "csv" if doc.output_format == "csv" else "json"
    return ReportDownloadRead(
        job_id=str(doc.id),
        content_type="text/csv" if ext == "csv" else "application/json",
        file_name=f"{doc.report_type}_{doc.id}.{ext}",
        content_base64=doc.file_content_base64,
        expires_at=doc.expires_at,
    )