"""Hostel reporting, exports and scheduling."""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.hostel_admin_models import HostelBed, HostelBedStatus
from app.modules.department_admin.csv_safe import encode_csv_base64, rows_to_csv
from app.modules.hostel.leave_outpass_models import HostelLeaveOutpassStatus, HostelOutpassRequest
from app.modules.hostel.maintenance_models import HostelComplaint, HostelComplaintStatus
from app.modules.hostel.mess_models import HostelMessEnrollment, MessEnrollmentStatus
from app.modules.hostel.policy import authorize_hostel_reports_export, authorize_hostel_reports_manage, authorize_hostel_reports_read, require_hostel_tenant_scope
from app.modules.hostel.reports_catalog import catalog_for_scope, catalog_item
from app.modules.hostel.reports_models import HostelReportExecutionHistory, HostelReportExportFormat, HostelSavedReport, HostelScheduledReport
from app.modules.hostel.reports_repository import HostelReportsRepository
from app.modules.hostel.reports_schemas import (
    HostelAnalyticsOverview,
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
from app.modules.hostel.resident_models import HostelResident, HostelResidentStatus
from app.modules.hostel.rules_incident_models import HostelIncident, HostelIncidentStatus
from app.modules.hostel.visitor_models import HostelVisitorEntry, HostelVisitorStatus

_repo = HostelReportsRepository()


def _authorize_report(scope: AccessScope, report_key: str) -> None:
    item = catalog_item(report_key)
    if item is None:
        raise AppError(code="NOT_FOUND", message="Unknown report", status_code=404)
    if Permission.HOSTEL_REPORTS_MANAGE not in scope.effective_permissions and Permission.HOSTEL_ADMIN_MANAGE not in scope.effective_permissions:
        authorize(scope, Permission(item.required_permission))
    if item.confidential and Permission.HOSTEL_INCIDENT_INVESTIGATE not in scope.effective_permissions:
        authorize(scope, Permission.HOSTEL_INCIDENT_INVESTIGATE)


async def report_catalog(scope: AccessScope) -> list[ReportCatalogItemRead]:
    authorize_hostel_reports_read(scope)
    items = catalog_for_scope(scope.effective_permissions)
    return [
        ReportCatalogItemRead(
            report_key=i.report_key,
            title=i.title,
            category=i.category,
            supported_formats=list(i.supported_formats),
            confidential=i.confidential,
        )
        for i in items
    ]


async def run_report(scope: AccessScope, payload: ReportRunRequest) -> ReportDataRead:
    tenant_id = require_hostel_tenant_scope(scope)
    _authorize_report(scope, payload.report_key)
    rows = await _repo.run_report(payload.report_key, tenant_id, payload.filters)
    if payload.report_key == "incidents_summary" and Permission.HOSTEL_INCIDENT_INVESTIGATE in scope.effective_permissions:
        pass
    elif catalog_item(payload.report_key) and catalog_item(payload.report_key).confidential:
        payload.filters["include_confidential"] = True
    return ReportDataRead(report_key=payload.report_key, row_count=len(rows), rows=rows)


async def export_report(scope: AccessScope, payload: ReportExportRequest) -> ReportExportRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_reports_export(scope)
    _authorize_report(scope, payload.report_key)
    fmt = payload.export_format
    if fmt not in (HostelReportExportFormat.CSV, HostelReportExportFormat.EXCEL):
        if fmt == HostelReportExportFormat.PDF:
            raise AppError(code="NOT_IMPLEMENTED", message="PDF export uses CSV placeholder in this phase", status_code=501)
    rows = await _repo.run_report(payload.report_key, tenant_id, payload.filters)
    execution_id = f"hex_{uuid4().hex[:10]}"
    csv_text = rows_to_csv(rows) if rows else ""
    b64 = encode_csv_base64(csv_text)
    await HostelReportExecutionHistory(
        tenant_id=tenant_id,
        execution_id=execution_id,
        report_key=payload.report_key,
        export_format=fmt,
        status="completed",
        row_count=len(rows),
        filters=payload.filters,
        file_content_base64=b64,
        actor_id=scope.user_id,
        completed_at=utcnow(),
    ).insert()
    return ReportExportRead(
        execution_id=execution_id,
        report_key=payload.report_key,
        export_format=fmt,
        status="completed",
        row_count=len(rows),
        file_content_base64=b64,
    )


async def upsert_saved_report(scope: AccessScope, payload: SavedReportUpsert) -> SavedReportRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_reports_manage(scope)
    _authorize_report(scope, payload.report_key)
    doc = await HostelSavedReport.find_one(
        Eq(HostelSavedReport.tenant_id, tenant_id),
        Eq(HostelSavedReport.owner_id, scope.user_id),
        Eq(HostelSavedReport.name, payload.name),
    )
    if doc:
        doc.report_key = payload.report_key
        doc.selected_fields = payload.selected_fields
        doc.filters = payload.filters
        doc.group_by = payload.group_by
        doc.sort_by = payload.sort_by
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = await HostelSavedReport(
            tenant_id=tenant_id,
            report_key=payload.report_key,
            name=payload.name,
            selected_fields=payload.selected_fields,
            filters=payload.filters,
            group_by=payload.group_by,
            sort_by=payload.sort_by,
            owner_id=scope.user_id,
        ).insert()
    return SavedReportRead(id=str(doc.id), report_key=doc.report_key, name=doc.name, filters=doc.filters)


async def upsert_scheduled_report(scope: AccessScope, payload: ScheduledReportUpsert) -> ScheduledReportRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_reports_manage(scope)
    _authorize_report(scope, payload.report_key)
    code = payload.schedule_code.strip().upper()
    saved_id = to_object_id(payload.saved_report_id, "saved_report_id") if payload.saved_report_id else None
    recipients = [to_object_id(uid, "recipient_user_id") for uid in payload.recipient_user_ids]
    doc = await HostelScheduledReport.find_one(
        Eq(HostelScheduledReport.tenant_id, tenant_id), Eq(HostelScheduledReport.schedule_code, code)
    )
    next_run = utcnow() + timedelta(days=1)
    if doc:
        doc.report_key = payload.report_key
        doc.saved_report_id = saved_id
        doc.frequency = payload.frequency
        doc.filters = payload.filters
        doc.export_format = payload.export_format
        doc.recipient_user_ids = recipients
        doc.delivery_channel = payload.delivery_channel
        doc.is_active = payload.is_active
        doc.next_run_at = next_run
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = await HostelScheduledReport(
            tenant_id=tenant_id,
            schedule_code=code,
            report_key=payload.report_key,
            saved_report_id=saved_id,
            frequency=payload.frequency,
            filters=payload.filters,
            export_format=payload.export_format,
            recipient_user_ids=recipients,
            delivery_channel=payload.delivery_channel,
            next_run_at=next_run,
            is_active=payload.is_active,
            actor_id=scope.user_id,
        ).insert()
    return ScheduledReportRead(
        schedule_code=doc.schedule_code,
        report_key=doc.report_key,
        frequency=doc.frequency,
        is_active=doc.is_active,
        last_status=doc.last_status,
    )


async def execute_scheduled_report(scope: AccessScope, schedule_code: str) -> ReportExportRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_reports_manage(scope)
    doc = await HostelScheduledReport.find_one(
        Eq(HostelScheduledReport.tenant_id, tenant_id), Eq(HostelScheduledReport.schedule_code, schedule_code.upper())
    )
    if doc is None or not doc.is_active:
        raise AppError(code="NOT_FOUND", message="Schedule not found", status_code=404)
    export = await export_report(
        scope,
        ReportExportRequest(report_key=doc.report_key, filters=doc.filters, export_format=doc.export_format),
    )
    doc.last_run_at = utcnow()
    doc.last_status = "completed"
    doc.next_run_at = utcnow() + timedelta(days=30)
    doc.updated_at = utcnow()
    await doc.save()
    return export


async def analytics_overview(scope: AccessScope) -> HostelAnalyticsOverview:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_reports_read(scope)
    overview = HostelAnalyticsOverview()
    beds = await HostelBed.find({"tenant_id": tenant_id}).to_list()
    overview.occupied_beds = sum(1 for b in beds if b.status == HostelBedStatus.ALLOCATED)
    overview.available_beds = sum(1 for b in beds if b.status == HostelBedStatus.AVAILABLE)
    overview.active_residents = await HostelResident.find(
        {"tenant_id": tenant_id, "status": HostelResidentStatus.CHECKED_IN.value}
    ).count()
    open_statuses = [
        HostelComplaintStatus.SUBMITTED.value,
        HostelComplaintStatus.ASSIGNED.value,
        HostelComplaintStatus.IN_PROGRESS.value,
    ]
    overview.open_complaints = await HostelComplaint.find({"tenant_id": tenant_id, "status": {"$in": open_statuses}}).count()
    overview.visitors_inside = await HostelVisitorEntry.find(
        {"tenant_id": tenant_id, "status": HostelVisitorStatus.INSIDE.value}
    ).count()
    overview.overdue_outpass = await HostelOutpassRequest.find(
        {"tenant_id": tenant_id, "status": HostelLeaveOutpassStatus.OVERDUE.value}
    ).count()
    overview.mess_enrollments_active = await HostelMessEnrollment.find(
        {"tenant_id": tenant_id, "status": MessEnrollmentStatus.ACTIVE.value}
    ).count()
    overview.open_incidents = await HostelIncident.find(
        {
            "tenant_id": tenant_id,
            "status": {"$nin": [HostelIncidentStatus.CLOSED.value, HostelIncidentStatus.DISMISSED.value]},
            "confidential": False,
        }
    ).count()
    return overview