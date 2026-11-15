"""Department Admin — scoped import/export jobs."""

from __future__ import annotations

from datetime import timedelta

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.department_admin.audit_helpers import record_department_audit
from app.modules.auth.models import User
from app.modules.department_admin.csv_safe import encode_csv_base64, parse_csv_base64, rows_to_csv
from app.modules.department_admin.department_scope import assert_course_in_department, assert_faculty_visible_to_department
from app.modules.department_admin.faculty_management_service import list_faculty_directory
from app.modules.department_admin.import_export_templates import EXPORT_DATASETS, IMPORT_TEMPLATES
from app.modules.department_admin.models import (
    DepartmentDataTransferJob,
    DepartmentDataTransferOperation,
    DepartmentDataTransferStatus,
    DepartmentFacultyAssignmentRequest,
    DepartmentRequestStatus,
)
from app.modules.department_admin.phase3_schemas import StudentDirectoryFilters
from app.modules.department_admin.phase8_schemas import (
    DataTransferJobRead,
    ExportDatasetRead,
    ExportRequestBody,
    ImportTemplateRead,
    ImportUploadBody,
    ReportDownloadRead,
    ReportFilters,
)
from app.modules.department_admin.policy import resolve_authorized_department
from app.modules.department_admin.student_administration_service import list_students

RETENTION_HOURS = 72


def list_import_templates(scope: AccessScope) -> list[ImportTemplateRead]:
    authorize(scope, Permission.DEPARTMENT_DATA_TRANSFER_READ)
    out: list[ImportTemplateRead] = []
    for tpl in IMPORT_TEMPLATES.values():
        if tpl.permission not in scope.effective_permissions:
            continue
        out.append(
            ImportTemplateRead(
                template_id=tpl.template_id,
                entity_type=tpl.entity_type,
                version=tpl.version,
                required_columns=sorted(tpl.required_columns),
                optional_columns=sorted(tpl.optional_columns),
                max_rows=tpl.max_rows,
                description=tpl.description,
                permission=tpl.permission.value,
            )
        )
    return out


def list_export_datasets(scope: AccessScope) -> list[ExportDatasetRead]:
    authorize(scope, Permission.DEPARTMENT_DATA_TRANSFER_READ)
    out: list[ExportDatasetRead] = []
    for ds in EXPORT_DATASETS.values():
        if ds.permission not in scope.effective_permissions:
            continue
        out.append(
            ExportDatasetRead(
                dataset_id=ds.dataset_id,
                description=ds.description,
                allowed_fields=sorted(ds.allowed_fields),
                default_fields=sorted(ds.default_fields),
                permission=ds.permission.value,
            )
        )
    return out


def _transfer_read(doc: DepartmentDataTransferJob) -> DataTransferJobRead:
    return DataTransferJobRead(
        job_id=str(doc.id),
        operation=doc.operation.value,
        dataset_type=doc.dataset_type,
        template_version=doc.template_version,
        status=doc.status,
        file_name=doc.file_name,
        valid_row_count=doc.valid_row_count,
        invalid_row_count=doc.invalid_row_count,
        executed_row_count=doc.executed_row_count,
        validation_summary=doc.validation_summary,
        expires_at=doc.expires_at,
        created_at=doc.created_at,
        completed_at=doc.completed_at,
        dry_run=doc.dry_run,
        has_download=bool(doc.export_file_base64),
    )


async def _validate_faculty_assignment_rows(
    tenant_id: PydanticObjectId,
    central_id: PydanticObjectId,
    rows: list[dict[str, str]],
    *,
    max_rows: int,
) -> tuple[list[dict], list[dict]]:
    errors: list[dict] = []
    valid: list[dict] = []
    for idx, row in enumerate(rows, start=2):
        if idx - 1 > max_rows:
            break
        missing = [c for c in IMPORT_TEMPLATES["faculty_course_assignment_rows"].required_columns if not row.get(c)]
        if missing:
            errors.append({"row": idx, "field": ",".join(missing), "category": "required", "message": "Missing required columns"})
            continue
        user = await User.find_one({"tenant_id": tenant_id, "email": row["faculty_email"].lower()})
        if user is None:
            errors.append({"row": idx, "field": "faculty_email", "category": "reference", "message": "Faculty user not found"})
            continue
        try:
            await assert_faculty_visible_to_department(tenant_id, central_id, user.id)
            await assert_course_in_department(tenant_id, central_id, row["course_code"])
        except AppError as exc:
            errors.append({"row": idx, "field": "scope", "category": "forbidden", "message": exc.message})
            continue
        valid.append({**row, "faculty_user_id": str(user.id)})
    return valid, errors


async def start_import(scope: AccessScope, user: User, body: ImportUploadBody) -> DataTransferJobRead:
    authorize(scope, Permission.DEPARTMENT_DATA_TRANSFER_MANAGE)
    tpl = IMPORT_TEMPLATES.get(body.template_id)
    if tpl is None:
        raise AppError(code="NOT_FOUND", message="Unknown import template", status_code=404)
    authorize(scope, tpl.permission)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    if body.idempotency_key:
        existing = await DepartmentDataTransferJob.find_one(
            Eq(DepartmentDataTransferJob.tenant_id, tenant_id),
            Eq(DepartmentDataTransferJob.idempotency_key, body.idempotency_key),
        )
        if existing and existing.central_department_id == central_id:
            return _transfer_read(existing)
    rows = parse_csv_base64(body.file_content_base64, max_rows=tpl.max_rows)
    valid, errors = await _validate_faculty_assignment_rows(tenant_id, central_id, rows, max_rows=tpl.max_rows)
    status = DepartmentDataTransferStatus.VALIDATED if not errors else DepartmentDataTransferStatus.VALIDATION_FAILED
    job = DepartmentDataTransferJob(
        tenant_id=tenant_id,
        central_department_id=central_id,
        requested_by=user.id,
        operation=DepartmentDataTransferOperation.IMPORT,
        dataset_type=body.template_id,
        template_version=tpl.version,
        status=status,
        file_name=body.file_name,
        file_content_base64=body.file_content_base64,
        validation_summary={"template_id": body.template_id, "total_rows": len(rows)},
        row_errors=errors,
        valid_row_count=len(valid),
        invalid_row_count=len(errors),
        dry_run=True,
        expires_at=utcnow() + timedelta(hours=RETENTION_HOURS),
        idempotency_key=body.idempotency_key,
    )
    job.validation_summary["valid_preview"] = valid[:20]
    await job.insert()
    await record_department_audit(
        actor_id=user.id,
        action="department.import.uploaded",
        resource_type="department_data_transfer_job",
        resource_id=str(job.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return _transfer_read(job)


async def validate_import_job(scope: AccessScope, user: User, job_id: str) -> DataTransferJobRead:
    authorize(scope, Permission.DEPARTMENT_DATA_TRANSFER_MANAGE)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await DepartmentDataTransferJob.get(to_object_id(job_id, "job_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Import job not found", status_code=404)
    if not doc.file_content_base64:
        raise AppError(code="CONFLICT", message="Import file missing", status_code=409)
    tpl = IMPORT_TEMPLATES.get(doc.dataset_type)
    if tpl is None:
        raise AppError(code="NOT_FOUND", message="Template no longer available", status_code=404)
    rows = parse_csv_base64(doc.file_content_base64, max_rows=tpl.max_rows)
    valid, errors = await _validate_faculty_assignment_rows(tenant_id, central_id, rows, max_rows=tpl.max_rows)
    doc.valid_row_count = len(valid)
    doc.invalid_row_count = len(errors)
    doc.row_errors = errors
    doc.status = DepartmentDataTransferStatus.VALIDATED if not errors else DepartmentDataTransferStatus.VALIDATION_FAILED
    doc.validation_summary = {"total_rows": len(rows), "valid_preview": valid[:20]}
    await doc.save()
    return _transfer_read(doc)


async def execute_import_job(scope: AccessScope, user: User, job_id: str) -> DataTransferJobRead:
    authorize(scope, Permission.DEPARTMENT_DATA_TRANSFER_MANAGE)
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await DepartmentDataTransferJob.get(to_object_id(job_id, "job_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Import job not found", status_code=404)
    if doc.status not in {DepartmentDataTransferStatus.VALIDATED, DepartmentDataTransferStatus.UPLOADED}:
        raise AppError(code="CONFLICT", message="Import is not validated for execution", status_code=409)
    if doc.executed_row_count > 0:
        raise AppError(code="CONFLICT", message="Import already executed", status_code=409)
    tpl = IMPORT_TEMPLATES.get(doc.dataset_type)
    if tpl is None:
        raise AppError(code="NOT_FOUND", message="Unknown template", status_code=404)
    rows = parse_csv_base64(doc.file_content_base64 or "", max_rows=tpl.max_rows)
    valid, errors = await _validate_faculty_assignment_rows(tenant_id, central_id, rows, max_rows=tpl.max_rows)
    if errors:
        doc.status = DepartmentDataTransferStatus.VALIDATION_FAILED
        doc.row_errors = errors
        await doc.save()
        raise AppError(code="VALIDATION_ERROR", message="Cannot execute import with validation errors", status_code=422)
    doc.status = DepartmentDataTransferStatus.EXECUTING
    await doc.save()
    created = 0
    for row in valid:
        faculty_oid = to_object_id(row["faculty_user_id"], "faculty_user_id")
        request = DepartmentFacultyAssignmentRequest(
            tenant_id=tenant_id,
            institution_department_id=institution.id,
            central_department_id=central_id,
            faculty_user_id=faculty_oid,
            request_type="assign",
            note=row.get("note"),
            status=DepartmentRequestStatus.PENDING,
            requested_by=user.id,
        )
        await request.insert()
        created += 1
    doc.executed_row_count = created
    doc.status = DepartmentDataTransferStatus.COMPLETED
    doc.completed_at = utcnow()
    doc.dry_run = False
    doc.file_content_base64 = None
    await doc.save()
    await record_department_audit(
        actor_id=user.id,
        action="department.import.executed",
        resource_type="department_data_transfer_job",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        metadata={"rows": created},
        central_department_id=central_id,
    )
    return _transfer_read(doc)


async def import_errors(scope: AccessScope, user: User, job_id: str) -> list[dict]:
    authorize(scope, Permission.DEPARTMENT_DATA_TRANSFER_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await DepartmentDataTransferJob.get(to_object_id(job_id, "job_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Import job not found", status_code=404)
    return doc.row_errors


async def start_export(scope: AccessScope, user: User, body: ExportRequestBody) -> DataTransferJobRead:
    authorize(scope, Permission.DEPARTMENT_DATA_TRANSFER_MANAGE)
    ds = EXPORT_DATASETS.get(body.dataset_id)
    if ds is None:
        raise AppError(code="NOT_FOUND", message="Unknown export dataset", status_code=404)
    authorize(scope, ds.permission)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    if body.idempotency_key:
        existing = await DepartmentDataTransferJob.find_one(
            Eq(DepartmentDataTransferJob.tenant_id, tenant_id),
            Eq(DepartmentDataTransferJob.idempotency_key, body.idempotency_key),
        )
        if existing and existing.central_department_id == central_id:
            return _transfer_read(existing)
    fields = body.fields or sorted(ds.default_fields)
    invalid = set(fields) - ds.allowed_fields
    if invalid:
        raise AppError(code="FORBIDDEN", message="Export includes disallowed fields", status_code=403)
    rows = await _export_rows(scope, user, body.dataset_id, body.filters)
    export_payload: str
    if body.output_format == "json":
        import json

        export_payload = encode_csv_base64(json.dumps([{k: r.get(k) for k in fields} for r in rows], default=str))
    else:
        export_payload = encode_csv_base64(rows_to_csv([{k: r.get(k) for k in fields} for r in rows], list(fields)))
    job = DepartmentDataTransferJob(
        tenant_id=tenant_id,
        central_department_id=central_id,
        requested_by=user.id,
        operation=DepartmentDataTransferOperation.EXPORT,
        dataset_type=body.dataset_id,
        template_version="1",
        status=DepartmentDataTransferStatus.COMPLETED,
        export_format=body.output_format,
        export_file_base64=export_payload,
        valid_row_count=len(rows),
        executed_row_count=len(rows),
        dry_run=False,
        expires_at=utcnow() + timedelta(hours=RETENTION_HOURS),
        idempotency_key=body.idempotency_key,
        completed_at=utcnow(),
        validation_summary={"fields": fields, "filters": body.filters.model_dump(mode="json")},
    )
    await job.insert()
    await record_department_audit(
        actor_id=user.id,
        action="department.export.created",
        resource_type="department_data_transfer_job",
        resource_id=str(job.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return _transfer_read(job)


async def _export_rows(scope: AccessScope, user: User, dataset_id: str, filters: ReportFilters) -> list[dict]:
    if dataset_id == "student_directory":
        page = await list_students(
            scope,
            user,
            filters=StudentDirectoryFilters(
                programme_code=filters.programme_code,
                batch_label=filters.batch_label,
                section_code=filters.section_code,
            ),
            pagination=Pagination(limit=5000, offset=0),
        )
        return [i.model_dump(mode="json") for i in page.items]
    if dataset_id == "faculty_directory":
        page = await list_faculty_directory(scope, user, pagination=Pagination(limit=2000, offset=0))
        return [
            {
                "faculty_user_id": i.faculty_user_id,
                "full_name": i.full_name,
                "email": i.email,
                "employee_id": i.employee_id,
                "designation": i.designation,
                "faculty_code": i.faculty_code,
            }
            for i in page.items
        ]
    if dataset_id == "faculty_workload_summary":
        page = await list_faculty_directory(scope, user, pagination=Pagination(limit=2000, offset=0))
        return [
            {
                "faculty_user_id": i.faculty_user_id,
                "full_name": i.full_name,
                "assignment_count": len(i.assigned_subjects),
                "academic_year_label": filters.academic_year_label,
                "semester_label": filters.semester_label,
            }
            for i in page.items
        ]
    raise AppError(code="NOT_FOUND", message="Dataset not supported", status_code=404)


async def get_transfer_job(scope: AccessScope, user: User, job_id: str) -> DataTransferJobRead:
    authorize(scope, Permission.DEPARTMENT_DATA_TRANSFER_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await DepartmentDataTransferJob.get(to_object_id(job_id, "job_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Job not found", status_code=404)
    if doc.expires_at and doc.expires_at < utcnow():
        doc.status = DepartmentDataTransferStatus.EXPIRED
        await doc.save()
    return _transfer_read(doc)


async def download_export_job(scope: AccessScope, user: User, job_id: str) -> ReportDownloadRead:
    authorize(scope, Permission.DEPARTMENT_DATA_TRANSFER_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await DepartmentDataTransferJob.get(to_object_id(job_id, "job_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Job not found", status_code=404)
    if doc.requested_by != user.id:
        authorize(scope, Permission.DEPARTMENT_DATA_TRANSFER_MANAGE)
    if doc.expires_at and doc.expires_at < utcnow():
        raise AppError(code="FORBIDDEN", message="Export expired", status_code=403)
    if not doc.export_file_base64:
        raise AppError(code="NOT_FOUND", message="No export artifact", status_code=404)
    fmt = doc.export_format or "csv"
    await record_department_audit(
        actor_id=user.id,
        action="department.export.downloaded",
        resource_type="department_data_transfer_job",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return ReportDownloadRead(
        job_id=str(doc.id),
        content_type="text/csv" if fmt == "csv" else "application/json",
        file_name=f"{doc.dataset_type}_{doc.id}.{fmt}",
        content_base64=doc.export_file_base64,
        expires_at=doc.expires_at,
    )


async def transfer_history(
    scope: AccessScope,
    user: User,
    *,
    operation: str | None,
    pagination: Pagination,
) -> Page[DataTransferJobRead]:
    authorize(scope, Permission.DEPARTMENT_DATA_TRANSFER_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    q: dict = {"tenant_id": tenant_id, "central_department_id": central_id}
    if operation:
        q["operation"] = operation
    db = DepartmentDataTransferJob.find(q).sort("-created_at")
    total = await db.count()
    rows = await db.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[_transfer_read(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)