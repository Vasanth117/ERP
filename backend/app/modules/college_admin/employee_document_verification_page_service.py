"""Employee document verification (CA 07.11)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import FacultyDocumentReference
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    EmployeeDocumentVerificationDecisionPayload,
    EmployeeDocumentVerificationPageRead,
    EmployeeDocumentVerificationTableRow,
    EmployeeDocumentVerificationVerifyAllPayload,
    InstitutionFieldOption,
    UserDashboardKpi,
)
from app.modules.hr.document_models import HrEmployeeDocument
from app.modules.hr.enums import HrEmployeeDocumentStatus

_IST = ZoneInfo("Asia/Kolkata")
_EXPIRY_DAYS = 60
_LIST_LIMIT = 50

_RESULT_OPTIONS = [
    InstitutionFieldOption(value="", label="Select result"),
    InstitutionFieldOption(value="verified", label="Verified"),
    InstitutionFieldOption(value="rejected", label="Rejected"),
]

_STATUS_PRESENTATION: dict[str, tuple[str, str]] = {
    "verified": ("Verified", "success"),
    "rejected": ("Rejected", "error"),
    "pending_verification": ("Pending", "warning"),
    "submitted": ("Pending", "warning"),
    "draft": ("Pending", "warning"),
    "pending": ("Pending", "warning"),
    "expired": ("Expiring", "warning"),
}


def _fmt_uploaded(when: datetime | date | None) -> str:
    if when is None:
        return "—"
    if isinstance(when, datetime):
        return as_utc_aware(when).astimezone(_IST).strftime("%d %b %Y")
    return when.strftime("%d %b %Y")


def _size_label(file_size: int | None) -> str | None:
    if not file_size:
        return None
    if file_size >= 1_048_576:
        return f"{file_size / 1_048_576:.1f} MB"
    if file_size >= 1024:
        return f"{int(file_size / 1024)} KB"
    return f"{file_size} B"


def _hr_row_key(doc_id: PydanticObjectId) -> str:
    return f"hr:{doc_id}"


def _faculty_row_key(doc_id: PydanticObjectId) -> str:
    return f"faculty:{doc_id}"


def _parse_row_key(raw: str | None) -> tuple[str, PydanticObjectId] | None:
    if not raw or ":" not in raw:
        return None
    kind, oid = raw.split(":", maxsplit=1)
    if kind not in {"hr", "faculty"}:
        return None
    return kind, to_object_id(oid, "document_id")


def _status_for_hr(status: HrEmployeeDocumentStatus) -> tuple[str, str]:
    key = status.value if isinstance(status, HrEmployeeDocumentStatus) else str(status)
    return _STATUS_PRESENTATION.get(key, (key.replace("_", " ").title(), "muted"))


async def _employee_name(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> str:
    user = await User.get(user_id)
    if user and user.tenant_id == tenant_id:
        return user.full_name
    return "—"


async def _compute_kpis(tenant_id: PydanticObjectId) -> list[UserDashboardKpi]:
    now = utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    today = now.date()
    expiry_cutoff = today + timedelta(days=_EXPIRY_DAYS)

    hr_docs = await HrEmployeeDocument.find(Eq(HrEmployeeDocument.tenant_id, tenant_id)).to_list()
    faculty_docs = await FacultyDocumentReference.find(Eq(FacultyDocumentReference.tenant_id, tenant_id)).to_list()

    pending_users: set[PydanticObjectId] = set()
    verified_month = 0
    expiring = 0
    rejected = 0

    for doc in hr_docs:
        if doc.status == HrEmployeeDocumentStatus.PENDING_VERIFICATION:
            pending_users.add(doc.employee_user_id)
        if doc.status == HrEmployeeDocumentStatus.REJECTED:
            rejected += 1
        if (
            doc.status == HrEmployeeDocumentStatus.VERIFIED
            and doc.verified_at
            and as_utc_aware(doc.verified_at) >= as_utc_aware(month_start)
        ):
            verified_month += 1
        if doc.expires_on and today <= doc.expires_on <= expiry_cutoff:
            expiring += 1

    for doc in faculty_docs:
        if not doc.authorized:
            pending_users.add(doc.user_id)

    return [
        UserDashboardKpi(
            key="pending",
            label="Pending verification",
            value=str(len(pending_users)),
            hint_line="Employees",
            hint_tone="warning" if pending_users else "success",
        ),
        UserDashboardKpi(
            key="verified_month",
            label="Verified this month",
            value=str(verified_month),
            hint_line="Documents",
            hint_tone="success",
        ),
        UserDashboardKpi(
            key="expiring",
            label="Expiring documents",
            value=str(expiring),
            hint_line=f"Within {_EXPIRY_DAYS} days",
            hint_tone="warning" if expiring else "muted",
        ),
        UserDashboardKpi(
            key="rejected",
            label="Rejected",
            value=str(rejected),
            hint_line="Resubmit",
            hint_tone="error" if rejected else "muted",
        ),
    ]


async def _collect_rows(
    tenant_id: PydanticObjectId,
) -> tuple[list[EmployeeDocumentVerificationTableRow], int]:
    rows: list[EmployeeDocumentVerificationTableRow] = []

    hr_docs = await HrEmployeeDocument.find(
        Eq(HrEmployeeDocument.tenant_id, tenant_id),
        In(
            HrEmployeeDocument.status,
            [
                HrEmployeeDocumentStatus.PENDING_VERIFICATION,
                HrEmployeeDocumentStatus.SUBMITTED,
                HrEmployeeDocumentStatus.VERIFIED,
                HrEmployeeDocumentStatus.REJECTED,
                HrEmployeeDocumentStatus.EXPIRED,
            ],
        ),
    ).sort("-updated_at").limit(_LIST_LIMIT).to_list()

    for doc in hr_docs:
        name = await _employee_name(tenant_id, doc.employee_user_id)
        label, tone = _status_for_hr(doc.status)
        uploaded = doc.submitted_at or doc.created_at
        rows.append(
            EmployeeDocumentVerificationTableRow(
                document_id=_hr_row_key(doc.id),
                employee_name=name,
                document_label=doc.title or doc.file_name,
                uploaded_label=_fmt_uploaded(uploaded),
                status_label=label,
                status_tone=tone,
            )
        )

    faculty_docs = await FacultyDocumentReference.find(Eq(FacultyDocumentReference.tenant_id, tenant_id)).sort(
        "-created_at"
    ).limit(_LIST_LIMIT).to_list()
    for doc in faculty_docs:
        name = await _employee_name(tenant_id, doc.user_id)
        if doc.authorized:
            label, tone = ("Verified", "success")
        else:
            label, tone = ("Pending", "warning")
        rows.append(
            EmployeeDocumentVerificationTableRow(
                document_id=_faculty_row_key(doc.id),
                employee_name=name,
                document_label=doc.label,
                uploaded_label=_fmt_uploaded(doc.created_at),
                status_label=label,
                status_tone=tone,
            )
        )

    rows.sort(key=lambda r: (0 if r.status_label == "Pending" else 1, r.uploaded_label))
    total = len(rows)
    return rows[:_LIST_LIMIT], total


async def get_employee_document_verification_page(
    scope: AccessScope,
    document_id: str | None = None,
) -> EmployeeDocumentVerificationPageRead:
    authorize(scope, Permission.FACULTY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    rows, total_count = await _collect_rows(tenant_id)
    kpis = await _compute_kpis(tenant_id)
    selected_key = document_id or (rows[0].document_id if rows else None)

    preview_file: str | None = None
    preview_meta: str | None = None
    decision_result = ""
    decision_remarks = ""

    parsed = _parse_row_key(selected_key)
    if parsed:
        kind, oid = parsed
        if kind == "hr":
            doc = await HrEmployeeDocument.get(oid)
            if doc and doc.tenant_id == tenant_id:
                preview_file = doc.file_name
                size = _size_label(doc.file_size)
                uploaded = _fmt_uploaded(doc.submitted_at or doc.created_at)
                preview_meta = f"Uploaded {uploaded}" + (f" · {size}" if size else "")
                if doc.status == HrEmployeeDocumentStatus.VERIFIED:
                    decision_result = "verified"
                elif doc.status == HrEmployeeDocumentStatus.REJECTED:
                    decision_result = "rejected"
                decision_remarks = doc.rejection_reason or ""
        elif kind == "faculty":
            doc = await FacultyDocumentReference.get(oid)
            if doc and doc.tenant_id == tenant_id:
                preview_file = f"{doc.label}.pdf"
                preview_meta = f"Uploaded {_fmt_uploaded(doc.created_at)}"
                decision_result = "verified" if doc.authorized else ""

    for row in rows:
        row.is_selected = row.document_id == selected_key

    showing = f"{len(rows)} of {total_count}" if total_count else "0 of 0"

    return EmployeeDocumentVerificationPageRead(
        page_title="Employee Document Verification",
        page_subtitle="Verify joining and qualification documents",
        request_document_label="Request document",
        request_document_href="/college-admin/faculty/employee-directory",
        verify_all_label="Verify all",
        kpis=kpis,
        documents_section_title="Documents",
        documents_footer_label=showing,
        table_headers=["Employee", "Document", "Uploaded", "Status"],
        document_rows=rows,
        preview_title="Preview",
        preview_empty_label="Select a document to preview.",
        preview_file_name=preview_file,
        preview_meta_label=preview_meta,
        browse_files_label="Browse files",
        browse_files_href=None,
        decision_section_title="Decision",
        result_field_label="Result",
        remarks_field_label="Remarks",
        result_options=_RESULT_OPTIONS,
        selected_document_id=selected_key,
        decision_result=decision_result,
        decision_remarks=decision_remarks,
        submit_decision_label="Save decision",
        footer_disclaimer="Live institutional data · Faculty and employee records · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )


async def save_employee_document_decision(
    scope: AccessScope,
    payload: EmployeeDocumentVerificationDecisionPayload,
) -> EmployeeDocumentVerificationPageRead:
    authorize(scope, Permission.FACULTY_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    actor_id = scope.user_id
    assert actor_id is not None

    result = (payload.result or "").strip().lower()
    if result not in {"verified", "rejected"}:
        raise AppError(code="VALIDATION_ERROR", message="Select Verified or Rejected", status_code=422)
    if result == "rejected" and not (payload.remarks or "").strip():
        raise AppError(code="VALIDATION_ERROR", message="Remarks are required for rejection", status_code=422)

    parsed = _parse_row_key(payload.document_id)
    if parsed is None:
        raise AppError(code="VALIDATION_ERROR", message="Invalid document", status_code=422)
    kind, oid = parsed

    if kind == "hr":
        doc = await HrEmployeeDocument.get(oid)
        if doc is None or doc.tenant_id != tenant_id:
            raise AppError(code="NOT_FOUND", message="Document not found", status_code=404)
        doc.status = (
            HrEmployeeDocumentStatus.VERIFIED if result == "verified" else HrEmployeeDocumentStatus.REJECTED
        )
        doc.rejection_reason = payload.remarks if result == "rejected" else None
        doc.verified_by = actor_id
        doc.verified_at = utcnow()
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = await FacultyDocumentReference.get(oid)
        if doc is None or doc.tenant_id != tenant_id:
            raise AppError(code="NOT_FOUND", message="Document not found", status_code=404)
        doc.authorized = result == "verified"
        doc.actor_id = actor_id
        await doc.save()

    return await get_employee_document_verification_page(scope, document_id=payload.document_id)


async def verify_all_employee_documents(
    scope: AccessScope,
    _: EmployeeDocumentVerificationVerifyAllPayload | None = None,
) -> EmployeeDocumentVerificationPageRead:
    authorize(scope, Permission.FACULTY_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    actor_id = scope.user_id
    assert actor_id is not None
    now = utcnow()

    pending_hr = await HrEmployeeDocument.find(
        Eq(HrEmployeeDocument.tenant_id, tenant_id),
        Eq(HrEmployeeDocument.status, HrEmployeeDocumentStatus.PENDING_VERIFICATION),
    ).to_list()
    for doc in pending_hr:
        doc.status = HrEmployeeDocumentStatus.VERIFIED
        doc.verified_by = actor_id
        doc.verified_at = now
        doc.updated_at = now
        await doc.save()

    pending_faculty = await FacultyDocumentReference.find(
        Eq(FacultyDocumentReference.tenant_id, tenant_id),
        Eq(FacultyDocumentReference.authorized, False),
    ).to_list()
    for doc in pending_faculty:
        doc.authorized = True
        doc.actor_id = actor_id
        await doc.save()

    return await get_employee_document_verification_page(scope, document_id=None)