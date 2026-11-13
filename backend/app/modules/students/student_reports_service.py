"""Personal student reports (scoped aggregates)."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.integrations.student_finance_reader import demands_for_student, ledger_for_student, payments_for_student
from app.modules.students.policy import require_student_scope
from app.modules.students.report_download_tokens import issue_report_download_token, resolve_report_download_token
from app.modules.students.report_storage import read_report_json, write_report_json
from app.modules.students.student_portal_enums import StudentReportExportStatus, StudentReportType
from app.modules.students.student_portal_models import StudentReportDownloadLog, StudentReportExport
from app.modules.students.student_portal_schemas import ReportExportRead, ReportGenerateInput

_reader = StudentDataReader()
_REPORT_TYPES = frozenset(t.value for t in StudentReportType)


async def _build_report(tenant_id: PydanticObjectId, user: User, report_type: StudentReportType) -> dict:
    context = await _reader.current_academic_context(tenant_id)
    year = context.academic_year_label if context else ""
    semester = context.semester_label if context else ""
    if report_type == StudentReportType.ATTENDANCE:
        summary = await _reader.attendance_summary(tenant_id, user.id, academic_year_label=year, semester_label=semester)
        return {"report_type": report_type.value, "academic_year": year, "semester": semester, "attendance": summary}
    if report_type == StudentReportType.FEE_SUMMARY:
        demands = await demands_for_student(tenant_id, user.id)
        payments = await payments_for_student(tenant_id, user.id)
        ledger = await ledger_for_student(tenant_id, user.id)
        return {
            "report_type": report_type.value,
            "demands": [{"demand_id": d.demand_id, "amount": d.amount, "status": d.status.value} for d in demands],
            "payments": [{"transaction_id": p.transaction_id, "amount": p.amount, "status": p.status.value} for p in payments[:50]],
            "ledger_balance": ledger[0].balance_after if ledger else 0,
        }
    if report_type == StudentReportType.COURSE_REGISTRATION:
        roster = await _reader.roster_entries(tenant_id, user.id, academic_year_label=year, semester_label=semester)
        return {
            "report_type": report_type.value,
            "courses": [{"course_code": r.course_code, "section": r.section_code} for r in roster],
        }
    if report_type == StudentReportType.ACADEMIC_SUMMARY:
        return {
            "report_type": report_type.value,
            "academic_year": year,
            "semester": semester,
            "enrollment_courses": len(await _reader.roster_entries(tenant_id, user.id, academic_year_label=year, semester_label=semester)),
        }
    if report_type == StudentReportType.EXAMINATION_PERFORMANCE:
        marks = await _reader.published_results(tenant_id, user.id, limit=100)
        return {
            "report_type": report_type.value,
            "published_results_count": len(marks),
        }
    return {"report_type": report_type.value}


async def generate_report(scope: AccessScope, user: User, payload: ReportGenerateInput) -> ReportExportRead:
    authorize(scope, Permission.STUDENT_REPORTS_MANAGE)
    tenant_id = require_student_scope(scope)
    if payload.report_type not in _REPORT_TYPES:
        raise AppError(code="VALIDATION_ERROR", message="Invalid report type", status_code=422)
    report_type = StudentReportType(payload.report_type)
    export_id = f"rpt_{uuid4().hex}"
    export = StudentReportExport(
        tenant_id=tenant_id,
        user_id=user.id,
        export_id=export_id,
        report_type=report_type,
        status=StudentReportExportStatus.PENDING,
    )
    await export.insert()
    try:
        body = await _build_report(tenant_id, user, report_type)
        storage_key = write_report_json(str(tenant_id), export_id, body)
        export.summary = {"rows": len(body.keys())}
        export.storage_key = storage_key
        export.status = StudentReportExportStatus.READY
        export.ready_at = utcnow()
        export.expires_at = utcnow() + timedelta(days=7)
    except Exception as exc:  # noqa: BLE001 — portal marks failed export
        export.status = StudentReportExportStatus.FAILED
        export.error_message = str(exc)[:500]
    await export.save()
    await record_audit(
        actor_id=scope.user_id,
        action="student.report.generated",
        resource_type="student_report_export",
        resource_id=export_id,
        tenant_id=tenant_id,
    )
    token = None
    if export.status == StudentReportExportStatus.READY:
        token = await issue_report_download_token(tenant_id=str(tenant_id), user_id=str(user.id), export_id=export_id)
    return ReportExportRead(
        export_id=export_id,
        report_type=report_type.value,
        status=export.status.value,
        created_at=export.created_at,
        ready_at=export.ready_at,
        download_token=token,
    )


async def report_status(scope: AccessScope, user: User, export_id: str) -> ReportExportRead:
    authorize(scope, Permission.STUDENT_REPORTS_READ)
    tenant_id = require_student_scope(scope)
    row = await StudentReportExport.find_one({"tenant_id": tenant_id, "user_id": user.id, "export_id": export_id})
    if row is None:
        raise AppError(code="NOT_FOUND", message="Report not found", status_code=404)
    token = None
    if row.status == StudentReportExportStatus.READY:
        token = await issue_report_download_token(tenant_id=str(tenant_id), user_id=str(user.id), export_id=export_id)
    return ReportExportRead(
        export_id=row.export_id,
        report_type=row.report_type.value,
        status=row.status.value,
        created_at=row.created_at,
        ready_at=row.ready_at,
        download_token=token,
    )


async def download_report(scope: AccessScope, user: User, export_id: str, token: str) -> dict:
    authorize(scope, Permission.STUDENT_REPORTS_READ)
    tenant_id = require_student_scope(scope)
    resolved = await resolve_report_download_token(tenant_id=str(tenant_id), token=token, user_id=str(user.id))
    if resolved != export_id:
        raise AppError(code="FORBIDDEN", message="Token does not match export", status_code=403)
    row = await StudentReportExport.find_one({"tenant_id": tenant_id, "user_id": user.id, "export_id": export_id})
    if row is None or row.status != StudentReportExportStatus.READY or not row.storage_key:
        raise AppError(code="NOT_FOUND", message="Report not available", status_code=404)
    data = read_report_json(row.storage_key)
    await StudentReportDownloadLog(tenant_id=tenant_id, user_id=user.id, export_id=export_id).insert()
    await record_audit(
        actor_id=scope.user_id,
        action="student.report.downloaded",
        resource_type="student_report_export",
        resource_id=export_id,
        tenant_id=tenant_id,
    )
    return data


async def report_history(scope: AccessScope, user: User, pagination: Pagination) -> Page[ReportExportRead]:
    authorize(scope, Permission.STUDENT_REPORTS_READ)
    tenant_id = require_student_scope(scope)
    total = await StudentReportExport.find({"tenant_id": tenant_id, "user_id": user.id}).count()
    rows = (
        await StudentReportExport.find({"tenant_id": tenant_id, "user_id": user.id})
        .sort("-created_at")
        .skip(pagination.offset)
        .limit(pagination.limit)
        .to_list()
    )
    items = [
        ReportExportRead(
            export_id=r.export_id,
            report_type=r.report_type.value,
            status=r.status.value,
            created_at=r.created_at,
            ready_at=r.ready_at,
            download_token=None,
        )
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)
