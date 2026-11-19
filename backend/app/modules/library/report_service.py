"""Library reports and analytics service."""

from datetime import datetime, timedelta, timezone
from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.department_admin.csv_safe import encode_csv_base64, rows_to_csv
from app.modules.library.policy import require_library_tenant_scope
from app.modules.library.report_access import (
    authorize_report_export,
    authorize_report_read,
    can_view_finance_reports,
    require_report_type,
)
from app.modules.library.report_catalog import LIBRARY_REPORT_CATALOG, catalog_for_role, catalog_item
from app.modules.library.report_filters import build_report_context
from app.modules.library.report_models import LibraryReportJob, LibraryReportJobStatus
from app.modules.library.report_repository import LibraryReportRepository
from app.modules.library.report_schemas import (
    LibraryReportCatalogItem,
    LibraryReportDataRead,
    LibraryReportDownloadRead,
    LibraryReportFilters,
    LibraryReportGenerateBody,
    LibraryReportJobRead,
)

RETENTION_HOURS = 72
_repo = LibraryReportRepository()


def _job_read(doc: LibraryReportJob) -> LibraryReportJobRead:
    return LibraryReportJobRead(
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


async def list_report_catalog(scope: AccessScope) -> list[LibraryReportCatalogItem]:
    authorize_report_read(scope)
    return catalog_for_role(can_finance=can_view_finance_reports(scope))


async def _build_report(scope: AccessScope, report_type: str, filters: LibraryReportFilters) -> LibraryReportDataRead:
    require_report_type(scope, report_type)
    tenant_id = require_library_tenant_scope(scope)
    ctx = await build_report_context(
        tenant_id,
        branch_code=filters.branch_code,
        category=filters.category,
        member_category=filters.member_category,
        status=filters.status,
        date_from=filters.date_from,
        date_to=filters.date_to,
    )
    rows, totals = await _repo.build(ctx, report_type)
    return LibraryReportDataRead(
        report_type=report_type,
        filters=filters,
        row_count=len(rows),
        totals=totals,
        rows=rows,
        generated_at=utcnow(),
    )


async def get_report_snapshot(scope: AccessScope, report_type: str, filters: LibraryReportFilters) -> LibraryReportDataRead:
    authorize_report_read(scope)
    return await _build_report(scope, report_type, filters)


async def generate_report_export(scope: AccessScope, user: User, body: LibraryReportGenerateBody) -> LibraryReportJobRead:
    authorize_report_export(scope)
    tenant_id = require_library_tenant_scope(scope)
    item = catalog_item(body.report_type)
    if item is None:
        raise AppError(code="NOT_FOUND", message="Unknown report type", status_code=404)
    if body.output_format not in item.supported_formats:
        raise AppError(code="VALIDATION_ERROR", message="Format not supported for this report", status_code=422)
    if body.idempotency_key:
        existing = await LibraryReportJob.find_one(
            Eq(LibraryReportJob.tenant_id, tenant_id),
            Eq(LibraryReportJob.idempotency_key, body.idempotency_key),
        )
        if existing:
            return _job_read(existing)
    expires = utcnow() + timedelta(hours=RETENTION_HOURS)
    job = LibraryReportJob(
        tenant_id=tenant_id,
        requested_by=user.id,
        report_type=body.report_type,
        filters=body.filters.model_dump(mode="json"),
        output_format=body.output_format,
        status=LibraryReportJobStatus.PROCESSING,
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
        job.status = LibraryReportJobStatus.COMPLETED
        job.completed_at = utcnow()
    except AppError:
        job.status = LibraryReportJobStatus.FAILED
        await job.save()
        raise
    except Exception as exc:
        job.status = LibraryReportJobStatus.FAILED
        job.error_message = "Report generation failed"
        await job.save()
        raise AppError(code="INTERNAL_ERROR", message="Report generation failed", status_code=500) from exc
    await job.save()
    await append_institution_audit(
        tenant_id,
        actor_id=user.id,
        action="library_report.generated",
        module="library_reports",
        resource_type="library_report_job",
        resource_id=str(job.id),
        metadata={"report_type": body.report_type, "row_count": job.row_count},
    )
    return _job_read(job)


async def download_report_export(scope: AccessScope, user: User, job_id: str) -> LibraryReportDownloadRead:
    authorize_report_export(scope)
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryReportJob.get(PydanticObjectId(job_id))
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Export job not found", status_code=404)
    if doc.requested_by != user.id and not can_view_finance_reports(scope):
        raise AppError(code="FORBIDDEN", message="Export access denied", status_code=403)
    if doc.expires_at:
        exp = doc.expires_at if doc.expires_at.tzinfo else doc.expires_at.replace(tzinfo=timezone.utc)
        if exp < utcnow():
            raise AppError(code="GONE", message="Export expired", status_code=410)
    if doc.status != LibraryReportJobStatus.COMPLETED:
        raise AppError(code="CONFLICT", message="Export not ready", status_code=409)
    return LibraryReportDownloadRead(
        job_id=str(doc.id),
        content_type="text/csv" if doc.output_format == "csv" else "application/json",
        file_name=f"{doc.report_type}_{doc.id}.{'csv' if doc.output_format == 'csv' else 'json'}",
        content_base64=doc.file_content_base64,
        row_count=doc.row_count,
    )


async def library_legacy_summary(scope: AccessScope, *, branch_code: str | None = None) -> dict:
    """College-admin legacy summary — delegates to overview report."""
    filters = LibraryReportFilters(branch_code=branch_code)
    data = await get_report_snapshot(scope, "overview", filters)
    row = data.rows[0] if data.rows else data.totals
    return {
        "branch_code": branch_code,
        "active_circulation": row.get("issued_copies", 0),
        "overdue_circulation": row.get("overdue_loans", 0),
        "open_fines": row.get("open_fines_count", 0),
        "total_copies": row.get("total_copies", 0),
        "available_copies": row.get("available_copies", 0),
    }