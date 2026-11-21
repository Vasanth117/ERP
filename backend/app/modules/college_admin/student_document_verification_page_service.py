"""Student document verification page (CA 06.07)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    InstitutionFieldOption,
    StudentDocumentVerificationDecisionPayload,
    StudentDocumentVerificationPageRead,
    StudentDocumentVerificationTableRow,
    UserDashboardKpi,
)
from app.modules.college_admin.student_admin_models import StudentAdmission, StudentRecord
from app.modules.college_admin.student_details_page_service import _document_rows
from app.modules.college_admin.student_statistics_overview_service import _normalize_meta_key
from app.modules.students.models import StudentProfile

_IST = ZoneInfo("Asia/Kolkata")

_RESULT_OPTIONS = [
    InstitutionFieldOption(value="", label="Select result"),
    InstitutionFieldOption(value="verified", label="Verified"),
    InstitutionFieldOption(value="needs_correction", label="Needs correction"),
    InstitutionFieldOption(value="rejected", label="Rejected"),
]

_STATUS_PRESENTATION: dict[str, tuple[str, str]] = {
    "verified": ("Verified", "success"),
    "approved": ("Verified", "success"),
    "needs_correction": ("Needs correction", "warning"),
    "rejected": ("Rejected", "error"),
    "pending": ("Pending", "warning"),
}


def _fmt_uploaded(raw: Any) -> str:
    if raw is None:
        return "—"
    if isinstance(raw, datetime):
        return raw.astimezone(_IST).strftime("%d %b %Y")
    if isinstance(raw, date):
        return raw.strftime("%d %b %Y")
    text = str(raw).strip()
    if not text:
        return "—"
    if "T" in text:
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(_IST).strftime("%d %b %Y")
        except ValueError:
            pass
    return text[:32]


def _size_label(meta: dict) -> str | None:
    kb = meta.get("size_kb") or meta.get("file_size_kb")
    if isinstance(kb, (int, float)):
        return f"{int(kb)} KB"
    raw = meta.get("file_size") or meta.get("size")
    if isinstance(raw, (int, float)):
        return f"{int(raw)} KB"
    return None


def _meta_doc_index(admission: StudentAdmission | None, document_key: str) -> int | None:
    if admission is None:
        return None
    meta_docs = admission.metadata.get("documents")
    if not isinstance(meta_docs, list):
        return None
    for index, item in enumerate(meta_docs):
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or item.get("name") or item.get("type") or f"Document {index + 1}")
        key = _normalize_meta_key(label) or f"doc_{index}"
        if key == document_key or _normalize_meta_key(str(item.get("document_key", ""))) == document_key:
            return index
    return None


def _collect_enriched_rows(
    profile: StudentProfile,
    admission: StudentAdmission | None,
) -> list[tuple[StudentDocumentVerificationTableRow, dict]]:
    base_rows = _document_rows(profile, admission)
    meta_by_key: dict[str, dict] = {}
    if admission:
        meta_docs = admission.metadata.get("documents")
        if isinstance(meta_docs, list):
            for index, item in enumerate(meta_docs):
                if not isinstance(item, dict):
                    continue
                label = str(item.get("label") or item.get("name") or item.get("type") or f"Document {index + 1}")
                key = _normalize_meta_key(label) or f"doc_{index}"
                meta_by_key[key] = item

    enriched: list[tuple[StudentDocumentVerificationTableRow, dict]] = []
    for row in base_rows:
        meta = meta_by_key.get(row.document_key, {})
        status_raw = str(meta.get("status") or "").lower()
        if row.status_label == "Verified":
            status_raw = status_raw or "verified"
        elif not status_raw:
            status_raw = "pending"
        label, tone = _STATUS_PRESENTATION.get(status_raw, (row.status_label, row.status_tone))
        file_name = meta.get("file_name") or meta.get("filename")
        if not file_name and row.document_label:
            file_name = f"{row.document_label}.pdf"
        enriched.append(
            (
                StudentDocumentVerificationTableRow(
                    document_key=row.document_key,
                    document_label=row.document_label,
                    uploaded_label=_fmt_uploaded(meta.get("uploaded_at") or meta.get("uploaded_label") or row.uploaded_label),
                    status_label=label,
                    status_tone=tone,
                    verified_by_label=row.verified_by_label if row.verified_by_label != "—" else str(meta.get("verified_by_name") or meta.get("verified_by") or "—"),
                    file_name=str(file_name) if file_name else None,
                    file_size_label=_size_label(meta),
                    is_selected=False,
                ),
                meta,
            )
        )
    return enriched


async def _verifier_label(actor_id: PydanticObjectId | None) -> str:
    if actor_id is None:
        return "Admissions Office"
    user = await User.get(actor_id)
    if user is None:
        return "Admissions Office"
    return user.full_name or "Admissions Office"


async def _compute_kpis(tenant_id: PydanticObjectId) -> list[UserDashboardKpi]:
    records = await StudentRecord.find(Eq(StudentRecord.tenant_id, tenant_id)).to_list()
    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    profile_by_user = {p.user_id: p for p in profiles}
    admissions = await StudentAdmission.find(Eq(StudentAdmission.tenant_id, tenant_id)).to_list()
    admission_by_id = {a.id: a for a in admissions if a.id is not None}

    today = utcnow().astimezone(_IST).date()
    pending_students = 0
    verified_today = 0
    rejected_count = 0
    missing_students = 0

    for record in records:
        profile = profile_by_user.get(record.user_id) or StudentProfile(tenant_id=tenant_id, user_id=record.user_id)
        admission = admission_by_id.get(record.admission_id) if record.admission_id else None
        rows = _collect_enriched_rows(profile, admission)
        if not rows:
            missing_students += 1
            continue
        student_has_pending = False
        for table_row, meta in rows:
            status = str(meta.get("status") or table_row.status_label).lower()
            if table_row.status_label == "Pending" or status in ("pending", "needs_correction"):
                student_has_pending = True
            if status == "rejected":
                rejected_count += 1
            verified_at = meta.get("verified_at")
            if verified_at:
                try:
                    when = datetime.fromisoformat(str(verified_at).replace("Z", "+00:00")).astimezone(_IST).date()
                    if when == today:
                        verified_today += 1
                except ValueError:
                    pass
            elif table_row.status_label == "Verified" and meta.get("verified_on") == today.isoformat():
                verified_today += 1
        if student_has_pending:
            pending_students += 1

    return [
        UserDashboardKpi(
            key="pending_verification",
            label="Pending verification",
            value=f"{pending_students:,}",
            hint_line="Students",
            hint_tone="warning" if pending_students else "muted",
        ),
        UserDashboardKpi(
            key="verified_today",
            label="Verified today",
            value=f"{verified_today:,}",
            hint_line="Documents",
            hint_tone="success" if verified_today else "muted",
        ),
        UserDashboardKpi(
            key="rejected",
            label="Rejected",
            value=f"{rejected_count:,}",
            hint_line="Resubmission needed" if rejected_count else "None",
            hint_tone="error" if rejected_count else "muted",
        ),
        UserDashboardKpi(
            key="missing_documents",
            label="Missing documents",
            value=f"{missing_students:,}",
            hint_line="Students without files",
            hint_tone="warning" if missing_students else "muted",
        ),
    ]


async def _build_page(
    scope: AccessScope,
    *,
    record_id: PydanticObjectId | None,
    document_key: str | None,
) -> StudentDocumentVerificationPageRead:
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    kpis = await _compute_kpis(tenant_id)

    if record_id is None:
        return StudentDocumentVerificationPageRead(
            page_title="Student Document Verification",
            page_subtitle="Review and verify submitted documents",
            request_document_label="Request document",
            request_document_href="/college-admin/students/profile-corrections",
            verify_all_label="Verify all",
            kpis=kpis,
            documents_section_title="Documents",
            documents_footer_label="Select a student from profile management",
            table_headers=["Document", "Uploaded", "Status", "Verified by"],
            document_rows=[],
            preview_title="Preview",
            preview_empty_label="Select a student to preview submitted files.",
            browse_files_label="Browse files",
            decision_section_title="Decision",
            result_field_label="Result",
            remarks_field_label="Remarks",
            result_options=_RESULT_OPTIONS,
            submit_decision_label="Save decision",
            footer_disclaimer="Live institutional data · Student documents and admissions records · All times IST",
            footer_snapshot_label="Snapshot",
            generated_at=now,
        )

    record = await StudentRecord.get(record_id)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Student record not found", status_code=404)
    user = await User.get(record.user_id)
    if user is None:
        raise AppError(code="NOT_FOUND", message="Student not found", status_code=404)

    profile = await StudentProfile.find_one(
        Eq(StudentProfile.tenant_id, tenant_id),
        Eq(StudentProfile.user_id, record.user_id),
    )
    if profile is None:
        profile = StudentProfile(tenant_id=tenant_id, user_id=record.user_id)
    admission = await StudentAdmission.get(record.admission_id) if record.admission_id else None

    enriched = _collect_enriched_rows(profile, admission)
    selected_key = document_key
    if not selected_key:
        for row, _ in enriched:
            if row.status_label in ("Pending", "Needs correction"):
                selected_key = row.document_key
                break
        if not selected_key and enriched:
            selected_key = enriched[0][0].document_key

    table_rows: list[StudentDocumentVerificationTableRow] = []
    selected_meta: dict = {}
    for row, meta in enriched:
        row.is_selected = row.document_key == selected_key
        table_rows.append(row)
        if row.is_selected:
            selected_meta = meta

    preview_file = selected_meta.get("file_name") or (table_rows and table_rows[0].file_name)
    uploaded = _fmt_uploaded(selected_meta.get("uploaded_at") or selected_meta.get("uploaded_label"))
    size = _size_label(selected_meta)
    preview_meta = " · ".join(part for part in (f"Uploaded {uploaded}" if uploaded != "—" else None, size) if part)

    return StudentDocumentVerificationPageRead(
        page_title="Student Document Verification",
        page_subtitle=f"Review and verify submitted documents for {user.full_name}",
        request_document_label="Request document",
        request_document_href="/college-admin/students/profile-corrections",
        verify_all_label="Verify all",
        record_id=str(record.id),
        student_name=user.full_name,
        profile_href=f"/college-admin/students/student-profile-management?record_id={record.id}",
        kpis=kpis,
        documents_section_title="Documents",
        documents_footer_label=f"{len(table_rows)} document{'s' if len(table_rows) != 1 else ''}",
        table_headers=["Document", "Uploaded", "Status", "Verified by"],
        document_rows=table_rows,
        preview_title="Preview",
        preview_empty_label="No document selected.",
        preview_file_name=str(preview_file) if preview_file else None,
        preview_meta_label=preview_meta or None,
        browse_files_label="Browse files",
        browse_files_href=None,
        decision_section_title="Decision",
        result_field_label="Result",
        remarks_field_label="Remarks",
        result_options=_RESULT_OPTIONS,
        selected_document_key=selected_key,
        decision_result=str(selected_meta.get("status") or ""),
        decision_remarks=str(selected_meta.get("remarks") or ""),
        submit_decision_label="Save decision",
        footer_disclaimer="Live institutional data · Student documents and admissions records · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )


async def get_student_document_verification_page(
    scope: AccessScope,
    record_id: str | None = None,
    document_key: str | None = None,
) -> StudentDocumentVerificationPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_READ)
    rid = to_object_id(record_id, "record_id") if record_id else None
    return await _build_page(scope, record_id=rid, document_key=document_key or None)


async def _apply_result_to_documents(
    *,
    admission: StudentAdmission | None,
    profile: StudentProfile,
    document_key: str,
    result: str,
    remarks: str | None,
    actor_id: PydanticObjectId | None,
) -> None:
    verifier = await _verifier_label(actor_id)
    now_iso = utcnow().isoformat()
    if admission is not None:
        meta = dict(admission.metadata or {})
        docs = meta.get("documents")
        if not isinstance(docs, list):
            docs = []
        index = _meta_doc_index(admission, document_key)
        if index is not None:
            item = dict(docs[index])
            item["status"] = result
            item["verified"] = result == "verified"
            item["verified_by_name"] = verifier if result == "verified" else item.get("verified_by_name")
            item["verified_at"] = now_iso if result == "verified" else item.get("verified_at")
            if remarks:
                item["remarks"] = remarks
            docs[index] = item
            meta["documents"] = docs
            admission.metadata = meta
            admission.updated_at = utcnow()
            await admission.save()

    for ref in profile.document_refs:
        key = ref.document_type or _normalize_meta_key(ref.label)
        if key == document_key or ref.label == document_key:
            ref.authorized = result == "verified"


async def save_document_verification_decision(
    scope: AccessScope,
    payload: StudentDocumentVerificationDecisionPayload,
) -> StudentDocumentVerificationPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    result = (payload.result or "").strip().lower()
    if result not in {"verified", "needs_correction", "rejected"}:
        raise AppError(code="VALIDATION_ERROR", message="Select a valid verification result", status_code=422)

    record_id = to_object_id(payload.record_id, "record_id")
    record = await StudentRecord.get(record_id)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Student record not found", status_code=404)

    profile = await StudentProfile.find_one(
        Eq(StudentProfile.tenant_id, tenant_id),
        Eq(StudentProfile.user_id, record.user_id),
    )
    if profile is None:
        profile = StudentProfile(tenant_id=tenant_id, user_id=record.user_id)
        await profile.insert()

    admission = await StudentAdmission.get(record.admission_id) if record.admission_id else None
    await _apply_result_to_documents(
        admission=admission,
        profile=profile,
        document_key=payload.document_key,
        result=result,
        remarks=payload.remarks,
        actor_id=scope.user_id,
    )
    if profile.id:
        profile.updated_at = utcnow()
        await profile.save()

    from app.modules.audit.service import record_audit

    await record_audit(
        actor_id=scope.user_id,
        action="student.document.verification_decision",
        resource_type="student_record",
        resource_id=str(record.id),
        tenant_id=tenant_id,
        metadata={"document_key": payload.document_key, "result": result, "remarks": payload.remarks},
    )
    return await _build_page(scope, record_id=record_id, document_key=payload.document_key)


async def verify_all_student_documents(scope: AccessScope, record_id: str) -> StudentDocumentVerificationPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    rid = to_object_id(record_id, "record_id")
    record = await StudentRecord.get(rid)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Student record not found", status_code=404)

    profile = await StudentProfile.find_one(
        Eq(StudentProfile.tenant_id, tenant_id),
        Eq(StudentProfile.user_id, record.user_id),
    )
    if profile is None:
        profile = StudentProfile(tenant_id=tenant_id, user_id=record.user_id)
        await profile.insert()
    admission = await StudentAdmission.get(record.admission_id) if record.admission_id else None

    pending = [
        row.document_key
        for row, _ in _collect_enriched_rows(profile, admission)
        if row.status_label in ("Pending", "Needs correction")
    ]
    for key in pending:
        if record.admission_id:
            admission = await StudentAdmission.get(record.admission_id)
        await _apply_result_to_documents(
            admission=admission,
            profile=profile,
            document_key=key,
            result="verified",
            remarks=None,
            actor_id=scope.user_id,
        )
    if profile.id:
        profile.updated_at = utcnow()
        await profile.save()

    return await _build_page(scope, record_id=rid, document_key=None)