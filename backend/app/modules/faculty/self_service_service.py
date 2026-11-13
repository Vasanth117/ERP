"""Faculty personal self-service and reports."""

import json

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.modules.attendance.models import AttendanceSession
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.examinations.models import MarksCorrectionRequest, MarksSubmissionBatch
from app.modules.faculty.integrations.notification_dispatch import integration_available
from app.modules.faculty.models import FacultyActivityLog, FacultyProfile, FacultyWorkload
from app.modules.faculty.policy import require_faculty_scope
from app.modules.faculty.profile_service import ensure_faculty_profile
from app.modules.faculty.report_tokens import default_expiry, hash_token, issue_token, sign_download
from app.modules.faculty.self_service_models import FacultyDocumentAccessLog, FacultyPersonalDocument, FacultyReportExport
from app.modules.faculty.self_service_schemas import (
    EmploymentInfoRead,
    LeaveRequestCreate,
    LeaveRequestRead,
    PayslipListRead,
    PersonalActivityHistoryItem,
    PersonalDocumentRead,
    ReportExportRead,
    WorkloadReportRead,
)
from app.modules.hr.enums import LeaveRequestStatus
from app.modules.hr.models import EmployeeProfileSnapshot, LeaveRequest, PayslipReference
from app.modules.lms import storage as lms_storage


async def get_employment_info(scope: AccessScope, user: User) -> EmploymentInfoRead:
    authorize(scope, Permission.FACULTY_SELF_SERVICE_READ)
    tenant_id = require_faculty_scope(scope)
    snapshot = await EmployeeProfileSnapshot.find_one({"tenant_id": tenant_id, "employee_user_id": user.id})
    if snapshot is not None:
        return EmploymentInfoRead(
            status="available",
            data={
                "employee_id": snapshot.employee_id,
                "designation": snapshot.designation,
                "department_name": snapshot.department_name,
                "joining_date": snapshot.joining_date.isoformat() if snapshot.joining_date else None,
                "employment_type": snapshot.employment_type,
                **snapshot.permitted_fields,
            },
        )
    profile = await ensure_faculty_profile(scope, user)
    if profile.employment_snapshot:
        return EmploymentInfoRead(status="partial", data=profile.employment_snapshot)
    return EmploymentInfoRead(status="not_configured", data={})


async def submit_leave(scope: AccessScope, user: User, payload: LeaveRequestCreate) -> LeaveRequestRead:
    authorize(scope, Permission.FACULTY_SELF_SERVICE_MANAGE)
    tenant_id = require_faculty_scope(scope)
    if payload.end_date < payload.start_date:
        raise AppError(code="VALIDATION_ERROR", message="Leave end date must be on or after start date", status_code=422)
    req = LeaveRequest(
        tenant_id=tenant_id,
        employee_user_id=user.id,
        leave_type=payload.leave_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        reason=payload.reason.strip(),
        status=LeaveRequestStatus.SUBMITTED,
    )
    await req.insert()
    await record_audit(
        actor_id=scope.user_id,
        action="faculty.leave.submitted",
        resource_type="leave_request",
        resource_id=str(req.id),
        tenant_id=tenant_id,
    )
    return _leave_read(req)


def _leave_read(req: LeaveRequest) -> LeaveRequestRead:
    return LeaveRequestRead(
        id=str(req.id),
        leave_type=req.leave_type,
        start_date=req.start_date,
        end_date=req.end_date,
        reason=req.reason,
        status=req.status.value,
        created_at=req.created_at,
    )


async def list_leave_requests(
    scope: AccessScope,
    user: User,
    *,
    status: LeaveRequestStatus | None = None,
) -> list[LeaveRequestRead]:
    authorize(scope, Permission.FACULTY_SELF_SERVICE_READ)
    tenant_id = require_faculty_scope(scope)
    filters: dict = {"tenant_id": tenant_id, "employee_user_id": user.id}
    if status is not None:
        filters["status"] = status
    rows = await LeaveRequest.find(filters).sort("-created_at").to_list()
    return [_leave_read(r) for r in rows]


async def get_leave_status(scope: AccessScope, user: User, leave_id: PydanticObjectId) -> LeaveRequestRead:
    authorize(scope, Permission.FACULTY_SELF_SERVICE_READ)
    tenant_id = require_faculty_scope(scope)
    req = await LeaveRequest.get(leave_id)
    if req is None or str(req.tenant_id) != str(tenant_id) or str(req.employee_user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Leave request not found", status_code=404)
    return _leave_read(req)


async def list_payslips(scope: AccessScope, user: User) -> PayslipListRead:
    authorize(scope, Permission.FACULTY_SELF_SERVICE_READ)
    tenant_id = require_faculty_scope(scope)
    settings = get_settings()
    payroll_on = getattr(settings, "payroll_integration_enabled", False)
    provider = await integration_available("payroll")
    if not payroll_on and not provider:
        return PayslipListRead(status="unavailable", items=[])
    rows = await PayslipReference.find({"tenant_id": tenant_id, "employee_user_id": user.id}).sort("-published_at").to_list()
    return PayslipListRead(
        status="available",
        items=[
            {"id": str(r.id), "period_label": r.period_label, "published_at": r.published_at.isoformat()}
            for r in rows
        ],
    )


async def download_payslip(scope: AccessScope, user: User, payslip_id: PydanticObjectId) -> tuple[bytes, str]:
    authorize(scope, Permission.FACULTY_SELF_SERVICE_READ)
    tenant_id = require_faculty_scope(scope)
    row = await PayslipReference.get(payslip_id)
    if row is None or str(row.tenant_id) != str(tenant_id) or str(row.employee_user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Payslip not found", status_code=404)
    await _log_doc_access(tenant_id, user.id, str(payslip_id), "payslip", "download")
    return lms_storage.read_bytes(row.storage_key), f"payslip-{row.period_label}.pdf"


async def list_personal_documents(scope: AccessScope, user: User) -> list[PersonalDocumentRead]:
    authorize(scope, Permission.FACULTY_SELF_SERVICE_READ)
    tenant_id = require_faculty_scope(scope)
    rows = await FacultyPersonalDocument.find({"tenant_id": tenant_id, "faculty_user_id": user.id}).sort("-created_at").to_list()
    return [
        PersonalDocumentRead(
            id=str(r.id),
            label=r.label,
            file_name=r.file_name,
            mime_type=r.mime_type,
            document_type=r.document_type,
            created_at=r.created_at,
        )
        for r in rows
    ]


async def download_personal_document(
    scope: AccessScope, user: User, document_id: PydanticObjectId
) -> tuple[bytes, str, str]:
    authorize(scope, Permission.FACULTY_SELF_SERVICE_READ)
    tenant_id = require_faculty_scope(scope)
    doc = await FacultyPersonalDocument.get(document_id)
    if doc is None or str(doc.tenant_id) != str(tenant_id) or str(doc.faculty_user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Document not found", status_code=404)
    await _log_doc_access(tenant_id, user.id, str(document_id), "personal_document", "download")
    data = lms_storage.read_bytes(doc.storage_key)
    return data, doc.file_name, doc.mime_type


async def _log_doc_access(
    tenant_id: PydanticObjectId, faculty_user_id: PydanticObjectId, document_id: str, doc_type: str, action: str
) -> None:
    await FacultyDocumentAccessLog(
        tenant_id=tenant_id,
        faculty_user_id=faculty_user_id,
        document_id=document_id,
        document_type=doc_type,
        action=action,
    ).insert()


async def personal_activity_history(
    scope: AccessScope, user: User, pagination: Pagination
) -> Page[PersonalActivityHistoryItem]:
    authorize(scope, Permission.FACULTY_SELF_SERVICE_READ)
    tenant_id = require_faculty_scope(scope)
    query = FacultyActivityLog.find({"tenant_id": tenant_id, "user_id": user.id}).sort("-occurred_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            PersonalActivityHistoryItem(
                activity_type=r.activity_type.value,
                title=r.title,
                occurred_at=r.occurred_at,
                source_module=r.source_module,
            )
            for r in rows
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def attendance_submission_history(scope: AccessScope, user: User) -> list[dict]:
    authorize(scope, Permission.FACULTY_SELF_SERVICE_READ)
    tenant_id = require_faculty_scope(scope)
    rows = await AttendanceSession.find({"tenant_id": tenant_id, "faculty_user_id": user.id}).sort("-session_date").limit(100).to_list()
    return [
        {
            "id": str(r.id),
            "course_code": r.course_code,
            "section": r.section,
            "session_date": r.session_date.isoformat(),
            "status": r.status.value,
        }
        for r in rows
    ]


async def marks_submission_history(scope: AccessScope, user: User) -> dict:
    authorize(scope, Permission.FACULTY_SELF_SERVICE_READ)
    tenant_id = require_faculty_scope(scope)
    batches = await MarksSubmissionBatch.find({"tenant_id": tenant_id, "faculty_user_id": user.id}).sort("-updated_at").to_list()
    corrections = await MarksCorrectionRequest.find({"tenant_id": tenant_id, "faculty_user_id": user.id}).sort("-created_at").to_list()
    return {
        "batches": [
            {
                "id": str(b.id),
                "assessment_id": b.assessment_id,
                "component_id": b.component_id,
                "status": b.status.value,
            }
            for b in batches
        ],
        "corrections": [{"id": str(c.id), "status": c.status.value} for c in corrections],
    }


async def personal_workload_report(scope: AccessScope, user: User) -> WorkloadReportRead:
    authorize(scope, Permission.FACULTY_SELF_SERVICE_READ)
    tenant_id = require_faculty_scope(scope)
    rows = await FacultyWorkload.find({"tenant_id": tenant_id, "user_id": user.id}).sort("-computed_at").to_list()
    return WorkloadReportRead(
        items=[
            {
                "academic_year_label": r.academic_year_label,
                "semester_label": r.semester_label,
                "total_hours": r.total_hours,
                "active_course_count": r.active_course_count,
            }
            for r in rows
        ]
    )


async def generate_personal_activity_report(scope: AccessScope, user: User) -> ReportExportRead:
    authorize(scope, Permission.FACULTY_SELF_SERVICE_MANAGE)
    tenant_id = require_faculty_scope(scope)
    activities = await FacultyActivityLog.find({"tenant_id": tenant_id, "user_id": user.id}).sort("-occurred_at").limit(200).to_list()
    attendance = await attendance_submission_history(scope, user)
    marks = await marks_submission_history(scope, user)
    payload = {
        "activities": [
            {"type": a.activity_type.value, "title": a.title, "at": a.occurred_at.isoformat()}
            for a in activities
        ],
        "attendance_submissions": attendance,
        "marks_history": marks,
    }
    raw = issue_token()
    export = FacultyReportExport(
        tenant_id=tenant_id,
        faculty_user_id=user.id,
        report_type="personal_activity",
        payload=payload,
        download_token_hash=hash_token(raw),
        expires_at=default_expiry(),
    )
    await export.insert()
    key = lms_storage.storage_key_for(str(tenant_id), "faculty_reports", f"{export.id}.json")
    lms_storage.write_bytes(key, json.dumps(payload, default=str).encode("utf-8"))
    export.storage_key = key
    await export.save()
    await record_audit(
        actor_id=scope.user_id,
        action="faculty.report.generated",
        resource_type="faculty_report_export",
        resource_id=str(export.id),
        tenant_id=tenant_id,
    )
    sig = sign_download(
        export_id=str(export.id),
        tenant_id=str(tenant_id),
        user_id=str(user.id),
        expires_at=export.expires_at,
        raw=raw,
    )
    return ReportExportRead(
        id=str(export.id),
        report_type=export.report_type,
        status=export.status,
        generated_at=export.generated_at,
        download_url=(
            f"/api/v1/faculty/me/self-service/reports/{export.id}/download"
            f"?token={raw}&sig={sig}"
        ),
    )


async def get_report_export(scope: AccessScope, user: User, export_id: PydanticObjectId) -> ReportExportRead:
    authorize(scope, Permission.FACULTY_SELF_SERVICE_READ)
    tenant_id = require_faculty_scope(scope)
    export = await FacultyReportExport.get(export_id)
    if export is None or str(export.tenant_id) != str(tenant_id) or str(export.faculty_user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Report export not found", status_code=404)
    return ReportExportRead(
        id=str(export.id),
        report_type=export.report_type,
        status=export.status,
        generated_at=export.generated_at,
        download_url=None,
    )


async def download_report_export(
    scope: AccessScope,
    user: User,
    export_id: PydanticObjectId,
    raw_token: str,
    signature: str,
) -> bytes:
    authorize(scope, Permission.FACULTY_SELF_SERVICE_READ)
    tenant_id = require_faculty_scope(scope)
    export = await FacultyReportExport.get(export_id)
    if export is None or str(export.tenant_id) != str(tenant_id) or str(export.faculty_user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Report export not found", status_code=404)
    if export.download_token_hash != hash_token(raw_token):
        raise AppError(code="FORBIDDEN", message="Invalid download token", status_code=403)
    from app.modules.faculty.report_tokens import verify_download

    if export.expires_at:
        verify_download(
            export_id=str(export_id),
            tenant_id=str(tenant_id),
            user_id=str(user.id),
            expires_at=export.expires_at,
            raw=raw_token,
            sig=signature,
        )
    await _log_doc_access(tenant_id, user.id, str(export_id), "report_export", "download")
    if not export.storage_key:
        raise AppError(code="NOT_FOUND", message="Report file missing", status_code=404)
    return lms_storage.read_bytes(export.storage_key)
