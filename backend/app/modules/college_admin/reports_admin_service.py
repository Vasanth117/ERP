"""Institutional reports and analytics."""

import json
from datetime import timedelta
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.lms_admin_service import get_lms_operational_stats
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.report_export_tokens import issue_report_export_token, resolve_report_export_token
from app.modules.college_admin.reports_admin_models import (
    InstitutionAnalyticsSnapshot,
    InstitutionReportAccessLog,
    InstitutionReportDefinition,
    InstitutionReportExport,
    InstitutionReportFilter,
    InstitutionReportJob,
    ReportJobStatus,
)
from app.modules.college_admin.reports_admin_schemas import (
    AnalyticsSnapshotRead,
    DashboardAnalyticsRead,
    ReportDefinitionRead,
    ReportDefinitionUpsert,
    ReportExportCreate,
    ReportExportRead,
    ReportFilterCreate,
    ReportFilterRead,
    ReportGenerateRequest,
    ReportJobRead,
    ReportScheduleRequest,
)

_reader = OperationalDataReader()

_BUILTIN_DEFINITIONS: list[dict] = [
    {
        "report_key": "dashboard",
        "title": "Institutional dashboard",
        "required_permission": Permission.COLLEGE_DASHBOARD_READ.value,
        "data_classification": "internal",
    },
    {
        "report_key": "enrollment",
        "title": "Student enrollment",
        "required_permission": Permission.STUDENT_ADMIN_READ.value,
        "data_classification": "internal",
    },
    {
        "report_key": "attendance",
        "title": "Attendance summary",
        "required_permission": Permission.ATTENDANCE_ADMIN_READ.value,
        "data_classification": "internal",
    },
    {
        "report_key": "examination",
        "title": "Examination and results",
        "required_permission": Permission.EXAMINATION_ADMIN_READ.value,
        "data_classification": "internal",
    },
    {
        "report_key": "finance",
        "title": "Finance and fee collection",
        "required_permission": Permission.FINANCE_ADMIN_READ.value,
        "data_classification": "restricted_financial",
    },
    {
        "report_key": "hr",
        "title": "HR and workforce",
        "required_permission": Permission.HR_ADMIN_READ.value,
        "data_classification": "restricted_hr",
    },
    {
        "report_key": "library",
        "title": "Library operations",
        "required_permission": Permission.LIBRARY_ADMIN_READ.value,
        "data_classification": "internal",
    },
    {
        "report_key": "hostel",
        "title": "Hostel occupancy",
        "required_permission": Permission.HOSTEL_ADMIN_READ.value,
        "data_classification": "internal",
    },
    {
        "report_key": "lms_engagement",
        "title": "LMS engagement",
        "required_permission": Permission.LMS_ADMIN_READ.value,
        "data_classification": "internal",
    },
    {
        "report_key": "pending_approvals",
        "title": "Pending approvals",
        "required_permission": Permission.COLLEGE_DASHBOARD_READ.value,
        "data_classification": "internal",
    },
]


async def _ensure_definitions(tenant_id: PydanticObjectId) -> None:
    for item in _BUILTIN_DEFINITIONS:
        existing = await InstitutionReportDefinition.find_one(
            Eq(InstitutionReportDefinition.tenant_id, tenant_id),
            Eq(InstitutionReportDefinition.report_key, item["report_key"]),
        )
        if existing is None:
            await InstitutionReportDefinition(
                tenant_id=tenant_id,
                report_key=item["report_key"],
                title=item["title"],
                required_permission=item["required_permission"],
                data_classification=item["data_classification"],
            ).insert()


async def _log_access(
    tenant_id: PydanticObjectId,
    actor_id: PydanticObjectId,
    report_key: str,
    action: str,
    resource_id: str | None = None,
) -> None:
    await InstitutionReportAccessLog(
        tenant_id=tenant_id,
        report_key=report_key,
        action=action,
        resource_id=resource_id,
        actor_id=actor_id,
    ).insert()


def _permission_allowed(scope: AccessScope, permission_code: str) -> bool:
    try:
        authorize(scope, Permission(permission_code))
        return True
    except AppError:
        return False


async def _resolve_definition(tenant_id: PydanticObjectId, report_key: str) -> InstitutionReportDefinition:
    await _ensure_definitions(tenant_id)
    doc = await InstitutionReportDefinition.find_one(
        Eq(InstitutionReportDefinition.tenant_id, tenant_id),
        Eq(InstitutionReportDefinition.report_key, report_key),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Report definition not found", status_code=404)
    return doc


async def _aggregate_metrics(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    report_key: str,
    *,
    department_id: PydanticObjectId | None,
    academic_year_label: str | None,
    filters: dict,
) -> dict:
    year, semester = await _reader.current_academic_term(tenant_id)
    if academic_year_label:
        year = academic_year_label
    if report_key == "dashboard" or report_key == "enrollment":
        stats = await _reader.headcount_statistics(tenant_id, department_id=department_id)
        return {
            "academic_year_label": year or "unspecified",
            "semester_label": semester or "unspecified",
            "headcount": stats.model_dump(mode="json"),
        }
    if report_key == "attendance":
        summary = await _reader.attendance_summary(tenant_id)
        return {"attendance": summary.model_dump(mode="json")}
    if report_key == "examination":
        summary = await _reader.examination_summary(tenant_id, academic_year_label=year, semester_label=semester)
        return {"examinations": summary.model_dump(mode="json")}
    if report_key == "finance":
        if not _permission_allowed(scope, Permission.FINANCE_ADMIN_READ.value):
            raise AppError(code="FORBIDDEN", message="Financial report not permitted", status_code=403)
        summary = await _reader.finance_summary(tenant_id)
        return {"finance": summary.model_dump(mode="json")}
    if report_key == "hr":
        if not _permission_allowed(scope, Permission.HR_ADMIN_READ.value):
            raise AppError(code="FORBIDDEN", message="HR report not permitted", status_code=403)
        stats = await _reader.headcount_statistics(tenant_id, department_id=department_id)
        return {"hr_workforce": stats.model_dump(mode="json")}
    if report_key == "library":
        lib = await _reader.library_hostel_summary(tenant_id)
        return {"library": lib.get("library", lib)}
    if report_key == "hostel":
        lib = await _reader.library_hostel_summary(tenant_id)
        return {"hostel": lib.get("hostel", lib)}
    if report_key == "lms_engagement":
        stats = await get_lms_operational_stats(scope)
        return {"lms": stats.model_dump(mode="json")}
    if report_key == "pending_approvals":
        pending = await _reader.pending_approvals(tenant_id, department_id=department_id, limit=200)
        return {"pending_approvals": pending, "count": len(pending)}
    raise AppError(code="VALIDATION_ERROR", message="Unsupported report_key", status_code=422)


async def list_report_definitions(scope: AccessScope) -> list[ReportDefinitionRead]:
    authorize(scope, Permission.REPORTS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    await _ensure_definitions(tenant_id)
    docs = await InstitutionReportDefinition.find(Eq(InstitutionReportDefinition.tenant_id, tenant_id)).to_list()
    visible: list[ReportDefinitionRead] = []
    for d in docs:
        if _permission_allowed(scope, d.required_permission):
            visible.append(
                ReportDefinitionRead(
                    report_key=d.report_key,
                    title=d.title,
                    required_permission=d.required_permission,
                    description=d.description,
                    supports_schedule=d.supports_schedule,
                    data_classification=d.data_classification,
                )
            )
    return visible


async def upsert_report_definition(scope: AccessScope, payload: ReportDefinitionUpsert) -> ReportDefinitionRead:
    authorize(scope, Permission.REPORTS_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    key = payload.report_key.strip().lower()
    doc = await InstitutionReportDefinition.find_one(
        Eq(InstitutionReportDefinition.tenant_id, tenant_id),
        Eq(InstitutionReportDefinition.report_key, key),
    )
    if doc is None:
        doc = InstitutionReportDefinition(
            tenant_id=tenant_id,
            report_key=key,
            title=payload.title,
            required_permission=payload.required_permission,
            description=payload.description,
            supports_schedule=payload.supports_schedule,
            data_classification=payload.data_classification,
        )
        await doc.insert()
    else:
        doc.title = payload.title
        doc.required_permission = payload.required_permission
        doc.description = payload.description
        doc.supports_schedule = payload.supports_schedule
        doc.data_classification = payload.data_classification
        doc.updated_at = utcnow()
        await doc.save()
    return ReportDefinitionRead(
        report_key=doc.report_key,
        title=doc.title,
        required_permission=doc.required_permission,
        description=doc.description,
        supports_schedule=doc.supports_schedule,
        data_classification=doc.data_classification,
    )


async def save_report_filter(scope: AccessScope, user: User, payload: ReportFilterCreate) -> ReportFilterRead:
    authorize(scope, Permission.REPORTS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    await _resolve_definition(tenant_id, payload.report_key)
    if not _permission_allowed(scope, (await _resolve_definition(tenant_id, payload.report_key)).required_permission):
        raise AppError(code="FORBIDDEN", message="Report not permitted", status_code=403)
    fid = payload.filter_id.strip()
    dept = to_object_id(payload.department_id, "department_id") if payload.department_id else None
    campus = to_object_id(payload.campus_id, "campus_id") if payload.campus_id else None
    doc = await InstitutionReportFilter.find_one(
        Eq(InstitutionReportFilter.tenant_id, tenant_id),
        Eq(InstitutionReportFilter.filter_id, fid),
    )
    if doc is None:
        doc = InstitutionReportFilter(
            tenant_id=tenant_id,
            filter_id=fid,
            report_key=payload.report_key,
            department_id=dept,
            campus_id=campus,
            date_from=payload.date_from,
            date_to=payload.date_to,
            academic_year_label=payload.academic_year_label,
            parameters=payload.parameters,
            owner_id=user.id,
        )
        await doc.insert()
    else:
        if doc.owner_id and doc.owner_id != user.id:
            authorize(scope, Permission.REPORTS_ADMIN_MANAGE)
        doc.report_key = payload.report_key
        doc.department_id = dept
        doc.campus_id = campus
        doc.date_from = payload.date_from
        doc.date_to = payload.date_to
        doc.academic_year_label = payload.academic_year_label
        doc.parameters = payload.parameters
        await doc.save()
    return ReportFilterRead(
        filter_id=doc.filter_id,
        report_key=doc.report_key,
        department_id=str(doc.department_id) if doc.department_id else None,
        campus_id=str(doc.campus_id) if doc.campus_id else None,
        date_from=doc.date_from,
        date_to=doc.date_to,
        academic_year_label=doc.academic_year_label,
    )


def _job_read(doc: InstitutionReportJob) -> ReportJobRead:
    return ReportJobRead(
        job_id=doc.job_id,
        report_key=doc.report_key,
        filter_id=doc.filter_id,
        status=doc.status,
        error_message=doc.error_message,
        snapshot_id=doc.snapshot_id,
        schedule_cron=doc.schedule_cron,
        next_run_at=doc.next_run_at,
        created_at=doc.created_at,
        completed_at=doc.completed_at,
    )


async def generate_report(scope: AccessScope, user: User, payload: ReportGenerateRequest) -> ReportJobRead:
    authorize(scope, Permission.REPORTS_ADMIN_GENERATE)
    tenant_id = require_college_tenant_scope(scope)
    definition = await _resolve_definition(tenant_id, payload.report_key)
    if not _permission_allowed(scope, definition.required_permission):
        raise AppError(code="FORBIDDEN", message="Report not permitted", status_code=403)
    dept_oid = to_object_id(payload.department_id, "department_id") if payload.department_id else None
    campus_oid = to_object_id(payload.campus_id, "campus_id") if payload.campus_id else None
    filter_doc: InstitutionReportFilter | None = None
    if payload.filter_id:
        filter_doc = await InstitutionReportFilter.find_one(
            Eq(InstitutionReportFilter.tenant_id, tenant_id),
            Eq(InstitutionReportFilter.filter_id, payload.filter_id),
        )
        if filter_doc is None:
            raise AppError(code="NOT_FOUND", message="Report filter not found", status_code=404)
        if filter_doc.report_key != payload.report_key:
            raise AppError(code="VALIDATION_ERROR", message="Filter report_key mismatch", status_code=422)
        dept_oid = filter_doc.department_id or dept_oid
        campus_oid = filter_doc.campus_id or campus_oid
    if payload.date_from and payload.date_to and payload.date_from > payload.date_to:
        raise AppError(code="VALIDATION_ERROR", message="Invalid date range", status_code=422)
    job_id = f"job_{uuid4().hex[:12]}"
    job = InstitutionReportJob(
        tenant_id=tenant_id,
        job_id=job_id,
        report_key=payload.report_key,
        filter_id=payload.filter_id,
        status=ReportJobStatus.RUNNING,
        actor_id=user.id,
    )
    await job.insert()
    filters = {
        "department_id": str(dept_oid) if dept_oid else None,
        "campus_id": str(campus_oid) if campus_oid else None,
        "date_from": (filter_doc.date_from if filter_doc else payload.date_from),
        "date_to": (filter_doc.date_to if filter_doc else payload.date_to),
        "academic_year_label": (filter_doc.academic_year_label if filter_doc else payload.academic_year_label),
    }
    try:
        metrics = await _aggregate_metrics(
            scope,
            tenant_id,
            payload.report_key,
            department_id=dept_oid,
            academic_year_label=filters.get("academic_year_label"),
            filters=filters,
        )
        snapshot_id = f"snap_{uuid4().hex[:12]}"
        await InstitutionAnalyticsSnapshot(
            tenant_id=tenant_id,
            snapshot_id=snapshot_id,
            report_key=payload.report_key,
            metrics=metrics,
            filters=filters,
            generated_by=user.id,
        ).insert()
        job.status = ReportJobStatus.COMPLETED
        job.snapshot_id = snapshot_id
        job.completed_at = utcnow()
        await job.save()
        await _log_access(tenant_id, user.id, payload.report_key, "generate", job_id)
    except AppError as exc:
        job.status = ReportJobStatus.FAILED
        job.error_message = exc.message
        job.completed_at = utcnow()
        await job.save()
        await _log_access(tenant_id, user.id, payload.report_key, "generate_failed", job_id)
        raise
    except Exception as exc:  # noqa: BLE001
        job.status = ReportJobStatus.FAILED
        job.error_message = str(exc)[:500]
        job.completed_at = utcnow()
        await job.save()
        await _log_access(tenant_id, user.id, payload.report_key, "generate_failed", job_id)
        raise AppError(code="INTERNAL_ERROR", message="Report generation failed", status_code=500) from exc
    return _job_read(job)


async def get_report_job(scope: AccessScope, job_id: str) -> ReportJobRead:
    authorize(scope, Permission.REPORTS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    doc = await InstitutionReportJob.find_one(
        Eq(InstitutionReportJob.tenant_id, tenant_id),
        Eq(InstitutionReportJob.job_id, job_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Report job not found", status_code=404)
    return _job_read(doc)


async def list_report_jobs(scope: AccessScope, pagination: Pagination) -> Page[ReportJobRead]:
    authorize(scope, Permission.REPORTS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    query = InstitutionReportJob.find(Eq(InstitutionReportJob.tenant_id, tenant_id))
    total = await query.count()
    docs = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[_job_read(d) for d in docs], total=total, limit=pagination.limit, offset=pagination.offset)


async def get_report_snapshot(scope: AccessScope, snapshot_id: str) -> AnalyticsSnapshotRead:
    authorize(scope, Permission.REPORTS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    doc = await InstitutionAnalyticsSnapshot.find_one(
        Eq(InstitutionAnalyticsSnapshot.tenant_id, tenant_id),
        Eq(InstitutionAnalyticsSnapshot.snapshot_id, snapshot_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Snapshot not found", status_code=404)
    definition = await _resolve_definition(tenant_id, doc.report_key)
    if not _permission_allowed(scope, definition.required_permission):
        raise AppError(code="FORBIDDEN", message="Report not permitted", status_code=403)
    return AnalyticsSnapshotRead(
        snapshot_id=doc.snapshot_id,
        report_key=doc.report_key,
        metrics=doc.metrics,
        filters=doc.filters,
        generated_at=doc.generated_at,
    )


async def schedule_report(scope: AccessScope, user: User, payload: ReportScheduleRequest) -> ReportJobRead:
    authorize(scope, Permission.REPORTS_ADMIN_SCHEDULE)
    tenant_id = require_college_tenant_scope(scope)
    definition = await _resolve_definition(tenant_id, payload.report_key)
    if not definition.supports_schedule:
        raise AppError(code="VALIDATION_ERROR", message="Report does not support scheduling", status_code=422)
    if not _permission_allowed(scope, definition.required_permission):
        raise AppError(code="FORBIDDEN", message="Report not permitted", status_code=403)
    job_id = f"sched_{uuid4().hex[:12]}"
    job = InstitutionReportJob(
        tenant_id=tenant_id,
        job_id=job_id,
        report_key=payload.report_key,
        filter_id=payload.filter_id,
        status=ReportJobStatus.PENDING,
        schedule_cron=payload.schedule_cron,
        next_run_at=utcnow() + timedelta(days=1),
        actor_id=user.id,
    )
    await job.insert()
    await _log_access(tenant_id, user.id, payload.report_key, "schedule", job_id)
    return _job_read(job)


async def create_report_export(scope: AccessScope, user: User, payload: ReportExportCreate) -> ReportExportRead:
    authorize(scope, Permission.REPORTS_ADMIN_EXPORT)
    tenant_id = require_college_tenant_scope(scope)
    job = await InstitutionReportJob.find_one(
        Eq(InstitutionReportJob.tenant_id, tenant_id),
        Eq(InstitutionReportJob.job_id, payload.job_id),
    )
    if job is None or job.status != ReportJobStatus.COMPLETED or not job.snapshot_id:
        raise AppError(code="VALIDATION_ERROR", message="Completed report job required", status_code=422)
    snapshot = await InstitutionAnalyticsSnapshot.find_one(
        Eq(InstitutionAnalyticsSnapshot.tenant_id, tenant_id),
        Eq(InstitutionAnalyticsSnapshot.snapshot_id, job.snapshot_id),
    )
    if snapshot is None:
        raise AppError(code="NOT_FOUND", message="Snapshot not found", status_code=404)
    definition = await _resolve_definition(tenant_id, job.report_key)
    if not _permission_allowed(scope, definition.required_permission):
        raise AppError(code="FORBIDDEN", message="Report export not permitted", status_code=403)
    export_id = f"exp_{uuid4().hex[:12]}"
    storage_key = f"tenant/{tenant_id}/reports/{export_id}.{payload.format}"
    expires_at = utcnow() + timedelta(minutes=15)
    try:
        token, token_hash = await issue_report_export_token(
            tenant_id=str(tenant_id),
            user_id=str(user.id),
            export_id=export_id,
            job_id=payload.job_id,
        )
    except Exception:
        token = None
        token_hash = None
    doc = InstitutionReportExport(
        tenant_id=tenant_id,
        export_id=export_id,
        job_id=payload.job_id,
        format=payload.format,
        storage_key=storage_key,
        download_token_hash=token_hash,
        expires_at=expires_at,
        actor_id=user.id,
    )
    await doc.insert()
    await _log_access(tenant_id, user.id, job.report_key, "export", export_id)
    return ReportExportRead(
        export_id=export_id,
        job_id=payload.job_id,
        format=payload.format,
        download_token=token,
        expires_at=expires_at,
    )


async def download_report_export(scope: AccessScope, user: User, token: str) -> dict:
    authorize(scope, Permission.REPORTS_ADMIN_EXPORT)
    tenant_id = require_college_tenant_scope(scope)
    try:
        export_id, job_id = await resolve_report_export_token(
            tenant_id=str(tenant_id),
            token=token,
            user_id=str(user.id),
        )
    except AppError:
        raise
    except Exception as exc:
        raise AppError(code="FORBIDDEN", message="Export token unavailable", status_code=403) from exc
    doc = await InstitutionReportExport.find_one(
        Eq(InstitutionReportExport.tenant_id, tenant_id),
        Eq(InstitutionReportExport.export_id, export_id),
    )
    if doc is None or doc.job_id != job_id:
        raise AppError(code="NOT_FOUND", message="Export not found", status_code=404)
    job = await InstitutionReportJob.find_one(
        Eq(InstitutionReportJob.tenant_id, tenant_id),
        Eq(InstitutionReportJob.job_id, job_id),
    )
    if job is None or not job.snapshot_id:
        raise AppError(code="NOT_FOUND", message="Report job not found", status_code=404)
    snapshot = await InstitutionAnalyticsSnapshot.find_one(
        Eq(InstitutionAnalyticsSnapshot.tenant_id, tenant_id),
        Eq(InstitutionAnalyticsSnapshot.snapshot_id, job.snapshot_id),
    )
    if snapshot is None:
        raise AppError(code="NOT_FOUND", message="Snapshot not found", status_code=404)
    await _log_access(tenant_id, user.id, job.report_key, "download", export_id)
    return {
        "export_id": export_id,
        "format": doc.format,
        "payload": json.dumps(snapshot.metrics, default=str),
    }


async def get_dashboard_analytics(
    scope: AccessScope,
    *,
    department_id: str | None = None,
    academic_year_label: str | None = None,
) -> DashboardAnalyticsRead:
    authorize(scope, Permission.REPORTS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    dept_oid = to_object_id(department_id, "department_id") if department_id else None
    year, semester = await _reader.current_academic_term(tenant_id)
    if academic_year_label:
        year = academic_year_label
    year = year or "unspecified"
    semester = semester or "unspecified"
    headcount = await _reader.headcount_statistics(tenant_id, department_id=dept_oid)
    attendance = await _reader.attendance_summary(tenant_id)
    finance = None
    if _permission_allowed(scope, Permission.FINANCE_ADMIN_READ.value):
        finance = await _reader.finance_summary(tenant_id)
    lms = None
    if _permission_allowed(scope, Permission.LMS_ADMIN_READ.value):
        lms = (await get_lms_operational_stats(scope)).model_dump(mode="json")
    pending = await _reader.pending_approvals(tenant_id, department_id=dept_oid, limit=100)
    return DashboardAnalyticsRead(
        academic_year_label=year,
        semester_label=semester,
        headcount=headcount.model_dump(mode="json"),
        attendance=attendance.model_dump(mode="json"),
        finance_summary=finance.model_dump(mode="json") if finance is not None else None,
        lms_engagement=lms,
        pending_approvals=len(pending),
    )


async def list_failed_report_jobs(scope: AccessScope, *, limit: int = 20) -> list[ReportJobRead]:
    authorize(scope, Permission.REPORTS_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    docs = (
        await InstitutionReportJob.find(
            Eq(InstitutionReportJob.tenant_id, tenant_id),
            Eq(InstitutionReportJob.status, ReportJobStatus.FAILED),
        )
        .sort("-created_at")
        .limit(limit)
        .to_list()
    )
    return [_job_read(d) for d in docs]