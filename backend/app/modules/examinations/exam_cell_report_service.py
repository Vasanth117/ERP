"""Examination reports and analytics."""

from datetime import timedelta

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.department_admin.csv_safe import encode_csv_base64, rows_to_csv
from app.modules.examinations.exam_cell_policy import (
    authorize_examination_cell_report_export,
    authorize_examination_cell_report_read,
    require_examination_cell_tenant,
)
from app.modules.examinations.exam_cell_report_catalog import EXAM_REPORT_CATALOG, catalog_for_scope, catalog_item
from app.modules.examinations.exam_cell_report_filters import build_report_context
from app.modules.examinations.exam_cell_report_models import ExamReportJob, ExamReportJobStatus
from app.modules.examinations.exam_cell_report_repository import ExamReportRepository
from app.modules.examinations.exam_cell_report_schemas import (
    ExamReportCatalogItem,
    ExamReportDataRead,
    ExamReportDownloadRead,
    ExamReportFilters,
    ExamReportGenerateBody,
    ExamReportJobRead,
)

RETENTION_HOURS = 72
_repo = ExamReportRepository()


def _can_view_sensitive(scope: AccessScope) -> bool:
    return Permission.EXAMINATION_CELL_INCIDENT_INVESTIGATE in scope.effective_permissions or Permission.EXAMINATION_CELL_INCIDENT_MANAGE in scope.effective_permissions


def _job_read(doc: ExamReportJob) -> ExamReportJobRead:
    return ExamReportJobRead(
        job_id=str(doc.id),
        report_type=doc.report_type,
        output_format=doc.output_format,
        status=doc.status.value,
        row_count=doc.row_count,
        filters=doc.filters,
        expires_at=doc.expires_at,
        created_at=doc.created_at,
        completed_at=doc.completed_at,
        has_download=bool(doc.file_content_base64),
        error_message=doc.error_message,
    )


async def list_report_catalog(scope: AccessScope) -> list[ExamReportCatalogItem]:
    authorize_examination_cell_report_read(scope)
    return catalog_for_scope(can_view_sensitive=_can_view_sensitive(scope))


async def _build_report(scope: AccessScope, report_type: str, filters: ExamReportFilters) -> ExamReportDataRead:
    item = catalog_item(report_type)
    if item is None:
        raise AppError(code="NOT_FOUND", message="Unknown report type", status_code=404)
    if item.sensitive and not _can_view_sensitive(scope):
        raise AppError(code="FORBIDDEN", message="Sensitive report not permitted", status_code=403)
    tenant_id = require_examination_cell_tenant(scope)
    ctx = await build_report_context(tenant_id, filters)
    rows, totals = await _repo.build(ctx, report_type)
    return ExamReportDataRead(
        report_type=report_type,
        filters=filters,
        row_count=len(rows),
        totals=totals,
        rows=rows,
        generated_at=utcnow(),
    )


async def get_report_snapshot(scope: AccessScope, report_type: str, filters: ExamReportFilters) -> ExamReportDataRead:
    authorize_examination_cell_report_read(scope)
    return await _build_report(scope, report_type, filters)


async def generate_report_export(scope: AccessScope, user: User, body: ExamReportGenerateBody) -> ExamReportJobRead:
    authorize_examination_cell_report_export(scope)
    tenant_id = require_examination_cell_tenant(scope)
    item = catalog_item(body.report_type)
    if item is None:
        raise AppError(code="NOT_FOUND", message="Unknown report type", status_code=404)
    if body.output_format not in item.supported_formats:
        raise AppError(code="VALIDATION_ERROR", message="Format not supported", status_code=422)
    if body.idempotency_key:
        existing = await ExamReportJob.find_one(
            Eq(ExamReportJob.tenant_id, tenant_id),
            Eq(ExamReportJob.idempotency_key, body.idempotency_key),
        )
        if existing:
            return _job_read(existing)
    expires = utcnow() + timedelta(hours=RETENTION_HOURS)
    job = ExamReportJob(
        tenant_id=tenant_id,
        requested_by=user.id,
        report_type=body.report_type,
        filters=body.filters.model_dump(mode="json"),
        output_format=body.output_format,
        status=ExamReportJobStatus.PROCESSING,
        expires_at=expires,
        idempotency_key=body.idempotency_key,
    )
    await job.insert()
    try:
        data = await _build_report(scope, body.report_type, body.filters)
        job.row_count = data.row_count
        job.totals = data.totals
        if body.output_format == "csv" and data.rows:
            fields = list(data.rows[0].keys())
            job.file_content_base64 = encode_csv_base64(rows_to_csv(data.rows, fields))
        job.status = ExamReportJobStatus.COMPLETED
        job.completed_at = utcnow()
        await job.save()
    except Exception as exc:
        job.status = ExamReportJobStatus.FAILED
        job.error_message = str(exc)[:500]
        job.completed_at = utcnow()
        await job.save()
        raise
    return _job_read(job)


async def get_report_job(scope: AccessScope, job_id: str) -> ExamReportJobRead:
    authorize_examination_cell_report_read(scope)
    tenant_id = require_examination_cell_tenant(scope)
    doc = await ExamReportJob.get(job_id)
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Report job not found", status_code=404)
    return _job_read(doc)


async def download_report_job(scope: AccessScope, job_id: str) -> ExamReportDownloadRead:
    authorize_examination_cell_report_export(scope)
    tenant_id = require_examination_cell_tenant(scope)
    doc = await ExamReportJob.get(job_id)
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Report job not found", status_code=404)
    if not doc.file_content_base64:
        raise AppError(code="NOT_FOUND", message="No export file for this job", status_code=404)
    return ExamReportDownloadRead(
        job_id=str(doc.id),
        report_type=doc.report_type,
        output_format=doc.output_format,
        file_content_base64=doc.file_content_base64,
    )