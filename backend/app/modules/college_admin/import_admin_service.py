"""Institution data import and migration."""

from datetime import timedelta
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.import_admin_models import (
    ImportEntityType,
    ImportJobStatus,
    InstitutionImportJob,
    InstitutionImportMapping,
    InstitutionImportRowResult,
    InstitutionImportTemplate,
    InstitutionImportValidationError,
    InstitutionMigrationHistory,
)
from app.modules.college_admin.import_admin_schemas import (
    ImportApproveRequest,
    ImportErrorReportRead,
    ImportJobRead,
    ImportMappingRead,
    ImportMappingUpsert,
    ImportPreviewRead,
    ImportTemplateRead,
    ImportUploadRequest,
    ImportValidationReport,
    MigrationHistoryItem,
)
from app.modules.college_admin.import_error_tokens import issue_import_error_token, resolve_import_error_token
from app.modules.college_admin.import_file_utils import (
    file_checksum,
    parse_import_content,
    write_import_file,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.security_admin_service import append_institution_audit

_BUILTIN_TEMPLATES: list[dict] = [
    {
        "template_id": "students_v1",
        "entity_type": ImportEntityType.STUDENTS,
        "title": "Student roster",
        "required_columns": ["student_id", "email", "full_name"],
        "optional_columns": ["department_code", "programme"],
        "duplicate_key": "student_id",
    },
    {
        "template_id": "faculty_v1",
        "entity_type": ImportEntityType.FACULTY,
        "title": "Faculty roster",
        "required_columns": ["employee_id", "email", "full_name"],
        "optional_columns": ["department_code"],
        "duplicate_key": "employee_id",
    },
    {
        "template_id": "courses_v1",
        "entity_type": ImportEntityType.COURSES,
        "title": "Course catalog",
        "required_columns": ["course_code", "name"],
        "optional_columns": ["credit_units"],
        "duplicate_key": "course_code",
    },
]


async def _ensure_templates(tenant_id: PydanticObjectId) -> None:
    for item in _BUILTIN_TEMPLATES:
        exists = await InstitutionImportTemplate.find_one(
            Eq(InstitutionImportTemplate.tenant_id, tenant_id),
            Eq(InstitutionImportTemplate.template_id, item["template_id"]),
        )
        if exists:
            continue
        await InstitutionImportTemplate(
            tenant_id=tenant_id,
            template_id=item["template_id"],
            entity_type=item["entity_type"],
            title=item["title"],
            required_columns=item["required_columns"],
            optional_columns=item["optional_columns"],
        ).insert()


async def _template(tenant_id: PydanticObjectId, template_id: str) -> InstitutionImportTemplate:
    await _ensure_templates(tenant_id)
    doc = await InstitutionImportTemplate.find_one(
        Eq(InstitutionImportTemplate.tenant_id, tenant_id),
        Eq(InstitutionImportTemplate.template_id, template_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Import template not found", status_code=404)
    return doc


def _job_read(doc: InstitutionImportJob) -> ImportJobRead:
    return ImportJobRead(
        job_id=doc.job_id,
        template_id=doc.template_id,
        entity_type=doc.entity_type,
        status=doc.status,
        file_name=doc.file_name,
        total_rows=doc.total_rows,
        valid_rows=doc.valid_rows,
        invalid_rows=doc.invalid_rows,
        duplicate_rows=doc.duplicate_rows,
        executed_rows=doc.executed_rows,
        failed_rows=doc.failed_rows,
        progress_percent=doc.progress_percent,
        requires_approval=doc.requires_approval,
        approved_at=doc.approved_at,
        created_at=doc.created_at,
        completed_at=doc.completed_at,
    )


async def list_import_templates(scope: AccessScope) -> list[ImportTemplateRead]:
    authorize(scope, Permission.IMPORT_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    await _ensure_templates(tenant_id)
    docs = await InstitutionImportTemplate.find(Eq(InstitutionImportTemplate.tenant_id, tenant_id)).to_list()
    return [
        ImportTemplateRead(
            template_id=d.template_id,
            entity_type=d.entity_type,
            title=d.title,
            version=d.version,
            required_columns=d.required_columns,
            optional_columns=d.optional_columns,
            max_rows=d.max_rows,
            requires_approval=d.requires_approval,
        )
        for d in docs
    ]


async def upsert_import_mapping(scope: AccessScope, user: User, payload: ImportMappingUpsert) -> ImportMappingRead:
    authorize(scope, Permission.IMPORT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    await _template(tenant_id, payload.template_id)
    mid = payload.mapping_id.strip()
    doc = await InstitutionImportMapping.find_one(
        Eq(InstitutionImportMapping.tenant_id, tenant_id),
        Eq(InstitutionImportMapping.mapping_id, mid),
    )
    if doc is None:
        doc = InstitutionImportMapping(
            tenant_id=tenant_id,
            mapping_id=mid,
            template_id=payload.template_id,
            column_map=payload.column_map,
            duplicate_key_field=payload.duplicate_key_field,
            actor_id=user.id,
        )
        await doc.insert()
    else:
        doc.template_id = payload.template_id
        doc.column_map = payload.column_map
        doc.duplicate_key_field = payload.duplicate_key_field
        doc.actor_id = user.id
        doc.updated_at = utcnow()
        await doc.save()
    return ImportMappingRead(
        mapping_id=doc.mapping_id,
        template_id=doc.template_id,
        column_map=doc.column_map,
        duplicate_key_field=doc.duplicate_key_field,
    )


async def upload_import_file(scope: AccessScope, user: User, payload: ImportUploadRequest) -> ImportJobRead:
    authorize(scope, Permission.IMPORT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    template = await _template(tenant_id, payload.template_id)
    if await InstitutionImportJob.find_one(
        Eq(InstitutionImportJob.tenant_id, tenant_id),
        Eq(InstitutionImportJob.idempotency_key, payload.idempotency_key),
    ):
        raise AppError(code="CONFLICT", message="Duplicate idempotency key", status_code=409)
    raw, rows = parse_import_content(payload.content_base64, payload.file_name)
    checksum = file_checksum(raw)
    job_id = f"imp_{uuid4().hex[:12]}"
    storage_key = f"{tenant_id}/{job_id}/{payload.file_name}"
    write_import_file(storage_key, raw)
    job = InstitutionImportJob(
        tenant_id=tenant_id,
        job_id=job_id,
        idempotency_key=payload.idempotency_key,
        template_id=template.template_id,
        entity_type=template.entity_type,
        status=ImportJobStatus.UPLOADED,
        file_name=payload.file_name,
        storage_key=storage_key,
        file_checksum=checksum,
        total_rows=len(rows),
        requires_approval=template.requires_approval,
        actor_id=user.id,
    )
    await job.insert()
    await append_institution_audit(
        tenant_id,
        actor_id=user.id,
        action="import.uploaded",
        module="import",
        resource_type="import_job",
        resource_id=job_id,
        metadata={"rows": len(rows), "checksum": checksum},
    )
    return _job_read(job)


async def _apply_mapping(row: dict[str, str], column_map: dict[str, str]) -> dict[str, str]:
    if not column_map:
        return row
    mapped: dict[str, str] = {}
    for src, dest in column_map.items():
        if src in row:
            mapped[dest] = row[src]
    for k, v in row.items():
        mapped.setdefault(k, v)
    return mapped


async def validate_import_job(scope: AccessScope, user: User, job_id: str, *, mapping_id: str | None = None) -> ImportValidationReport:
    authorize(scope, Permission.IMPORT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    job = await InstitutionImportJob.find_one(
        Eq(InstitutionImportJob.tenant_id, tenant_id),
        Eq(InstitutionImportJob.job_id, job_id),
    )
    if job is None:
        raise AppError(code="NOT_FOUND", message="Import job not found", status_code=404)
    template = await _template(tenant_id, job.template_id)
    column_map: dict[str, str] = {}
    dup_field: str | None = None
    if mapping_id:
        mapping = await InstitutionImportMapping.find_one(
            Eq(InstitutionImportMapping.tenant_id, tenant_id),
            Eq(InstitutionImportMapping.mapping_id, mapping_id),
        )
        if mapping:
            job.mapping_id = mapping_id
            column_map = mapping.column_map
            dup_field = mapping.duplicate_key_field
    elif job.mapping_id:
        mapping = await InstitutionImportMapping.find_one(
            Eq(InstitutionImportMapping.tenant_id, tenant_id),
            Eq(InstitutionImportMapping.mapping_id, job.mapping_id),
        )
        if mapping:
            column_map = mapping.column_map
            dup_field = mapping.duplicate_key_field
    from app.modules.college_admin.import_file_utils import import_storage_base, parse_csv_bytes

    raw = (import_storage_base() / job.storage_key).read_bytes()
    rows = parse_csv_bytes(raw)
    await InstitutionImportValidationError.find(
        Eq(InstitutionImportValidationError.tenant_id, tenant_id),
        Eq(InstitutionImportValidationError.job_id, job_id),
    ).delete()
    await InstitutionImportRowResult.find(
        Eq(InstitutionImportRowResult.tenant_id, tenant_id),
        Eq(InstitutionImportRowResult.job_id, job_id),
    ).delete()
    builtin = next((t for t in _BUILTIN_TEMPLATES if t["template_id"] == template.template_id), {})
    dup_key = dup_field or builtin.get("duplicate_key")
    seen: set[str] = set()
    valid = invalid = dup = 0
    errors: list[dict] = []
    for idx, row in enumerate(rows, start=2):
        mapped = await _apply_mapping(row, column_map)
        missing = [c for c in template.required_columns if not mapped.get(c)]
        if missing:
            invalid += 1
            err = InstitutionImportValidationError(
                tenant_id=tenant_id,
                job_id=job_id,
                row_number=idx,
                field=",".join(missing),
                error_code="required",
                message="Missing required fields",
            )
            await err.insert()
            errors.append({"row": idx, "field": err.field, "message": err.message})
            await InstitutionImportRowResult(
                tenant_id=tenant_id,
                job_id=job_id,
                row_number=idx,
                status="invalid",
                payload=mapped,
                error_message=err.message,
            ).insert()
            continue
        if dup_key:
            key_val = mapped.get(dup_key, "")
            if key_val in seen:
                dup += 1
                err = InstitutionImportValidationError(
                    tenant_id=tenant_id,
                    job_id=job_id,
                    row_number=idx,
                    field=dup_key,
                    error_code="duplicate",
                    message="Duplicate key in file",
                )
                await err.insert()
                errors.append({"row": idx, "field": dup_key, "message": "duplicate"})
                await InstitutionImportRowResult(
                    tenant_id=tenant_id,
                    job_id=job_id,
                    row_number=idx,
                    status="duplicate",
                    payload=mapped,
                    error_message="duplicate",
                ).insert()
                continue
            seen.add(key_val)
        valid += 1
        await InstitutionImportRowResult(
            tenant_id=tenant_id,
            job_id=job_id,
            row_number=idx,
            status="valid",
            payload=mapped,
        ).insert()
    job.valid_rows = valid
    job.invalid_rows = invalid
    job.duplicate_rows = dup
    if job.requires_approval:
        job.status = ImportJobStatus.PENDING_APPROVAL if invalid == 0 else ImportJobStatus.PREVIEW_READY
    else:
        job.status = ImportJobStatus.VALIDATED if invalid == 0 else ImportJobStatus.PREVIEW_READY
    job.progress_percent = 25.0
    await job.save()
    await append_institution_audit(
        tenant_id,
        actor_id=user.id,
        action="import.validated",
        module="import",
        resource_type="import_job",
        resource_id=job_id,
        metadata={"valid": valid, "invalid": invalid, "duplicate": dup},
    )
    return ImportValidationReport(
        job_id=job_id,
        valid_rows=valid,
        invalid_rows=invalid,
        duplicate_rows=dup,
        errors=errors[:100],
    )


async def preview_import(scope: AccessScope, job_id: str, *, limit: int = 20) -> ImportPreviewRead:
    authorize(scope, Permission.IMPORT_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    rows = await InstitutionImportRowResult.find(
        Eq(InstitutionImportRowResult.tenant_id, tenant_id),
        Eq(InstitutionImportRowResult.job_id, job_id),
        Eq(InstitutionImportRowResult.status, "valid"),
    ).sort("+row_number").limit(limit + 1).to_list()
    truncated = len(rows) > limit
    return ImportPreviewRead(
        job_id=job_id,
        preview_rows=[r.payload for r in rows[:limit]],
        truncated=truncated,
    )


async def approve_import(scope: AccessScope, user: User, job_id: str, payload: ImportApproveRequest) -> ImportJobRead:
    authorize(scope, Permission.IMPORT_ADMIN_APPROVE)
    tenant_id = require_college_tenant_scope(scope)
    job = await InstitutionImportJob.find_one(
        Eq(InstitutionImportJob.tenant_id, tenant_id),
        Eq(InstitutionImportJob.job_id, job_id),
    )
    if job is None:
        raise AppError(code="NOT_FOUND", message="Import job not found", status_code=404)
    if not job.requires_approval:
        raise AppError(code="VALIDATION_ERROR", message="Job does not require approval", status_code=422)
    if job.status not in (ImportJobStatus.VALIDATED, ImportJobStatus.PREVIEW_READY, ImportJobStatus.PENDING_APPROVAL):
        raise AppError(code="VALIDATION_ERROR", message="Import must be validated before approval", status_code=422)
    if not payload.authorized:
        raise AppError(code="FORBIDDEN", message="Import not authorized", status_code=403)
    job.status = ImportJobStatus.APPROVED
    job.approved_by = user.id
    job.approved_at = utcnow()
    await job.save()
    await append_institution_audit(
        tenant_id,
        actor_id=user.id,
        action="import.approved",
        module="import",
        resource_type="import_job",
        resource_id=job_id,
    )
    return _job_read(job)


async def execute_import(scope: AccessScope, user: User, job_id: str) -> ImportJobRead:
    authorize(scope, Permission.IMPORT_ADMIN_EXECUTE)
    tenant_id = require_college_tenant_scope(scope)
    job = await InstitutionImportJob.find_one(
        Eq(InstitutionImportJob.tenant_id, tenant_id),
        Eq(InstitutionImportJob.job_id, job_id),
    )
    if job is None:
        raise AppError(code="NOT_FOUND", message="Import job not found", status_code=404)
    if job.requires_approval and job.status != ImportJobStatus.APPROVED:
        raise AppError(code="FORBIDDEN", message="Approved import required before execution", status_code=403)
    if not job.requires_approval and job.status not in (
        ImportJobStatus.VALIDATED,
        ImportJobStatus.PREVIEW_READY,
        ImportJobStatus.APPROVED,
    ):
        raise AppError(code="VALIDATION_ERROR", message="Import not ready for execution", status_code=422)
    if job.status == ImportJobStatus.UPLOADED:
        raise AppError(code="VALIDATION_ERROR", message="Validate import before execution", status_code=422)
    job.status = ImportJobStatus.RUNNING
    await job.save()
    valid_rows = await InstitutionImportRowResult.find(
        Eq(InstitutionImportRowResult.tenant_id, tenant_id),
        Eq(InstitutionImportRowResult.job_id, job_id),
        Eq(InstitutionImportRowResult.status, "valid"),
    ).to_list()
    executed = failed = 0
    rollback_batch: list[dict] = []
    for row in valid_rows:
        try:
            row.status = "imported"
            row.error_message = None
            await row.save()
            executed += 1
            rollback_batch.append({"row_number": row.row_number, "payload": row.payload})
        except Exception as exc:  # noqa: BLE001
            row.status = "failed"
            row.error_message = str(exc)[:200]
            await row.save()
            failed += 1
    job.executed_rows = executed
    job.failed_rows = failed
    job.progress_percent = 100.0
    job.completed_at = utcnow()
    job.rollback_token = f"rb_{uuid4().hex[:12]}"
    job.status = ImportJobStatus.COMPLETED if failed == 0 else ImportJobStatus.PARTIAL
    await job.save()
    migration_id = f"mig_{uuid4().hex[:12]}"
    await InstitutionMigrationHistory(
        tenant_id=tenant_id,
        migration_id=migration_id,
        job_id=job_id,
        action="import_execute",
        summary=f"Imported {executed} rows",
        compensating_action={"rollback_token": job.rollback_token, "rows": rollback_batch[:500]},
        actor_id=user.id,
    ).insert()
    await append_institution_audit(
        tenant_id,
        actor_id=user.id,
        action="import.executed",
        module="import",
        resource_type="import_job",
        resource_id=job_id,
        metadata={"executed": executed, "failed": failed},
    )
    return _job_read(job)


async def get_import_job(scope: AccessScope, job_id: str) -> ImportJobRead:
    authorize(scope, Permission.IMPORT_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    job = await InstitutionImportJob.find_one(
        Eq(InstitutionImportJob.tenant_id, tenant_id),
        Eq(InstitutionImportJob.job_id, job_id),
    )
    if job is None:
        raise AppError(code="NOT_FOUND", message="Import job not found", status_code=404)
    return _job_read(job)


async def retry_failed_import_rows(scope: AccessScope, user: User, job_id: str) -> ImportJobRead:
    authorize(scope, Permission.IMPORT_ADMIN_EXECUTE)
    tenant_id = require_college_tenant_scope(scope)
    job = await InstitutionImportJob.find_one(
        Eq(InstitutionImportJob.tenant_id, tenant_id),
        Eq(InstitutionImportJob.job_id, job_id),
    )
    if job is None:
        raise AppError(code="NOT_FOUND", message="Import job not found", status_code=404)
    failed_rows = await InstitutionImportRowResult.find(
        Eq(InstitutionImportRowResult.tenant_id, tenant_id),
        Eq(InstitutionImportRowResult.job_id, job_id),
        Eq(InstitutionImportRowResult.status, "failed"),
    ).to_list()
    recovered = 0
    for row in failed_rows:
        row.status = "imported"
        row.error_message = None
        await row.save()
        recovered += 1
    job.executed_rows += recovered
    job.failed_rows = max(0, job.failed_rows - recovered)
    if job.failed_rows == 0:
        job.status = ImportJobStatus.COMPLETED
    await job.save()
    await append_institution_audit(
        tenant_id,
        actor_id=user.id,
        action="import.retry",
        module="import",
        resource_type="import_job",
        resource_id=job_id,
        metadata={"recovered": recovered},
    )
    return _job_read(job)


async def list_migration_history(scope: AccessScope, pagination: Pagination) -> Page[MigrationHistoryItem]:
    authorize(scope, Permission.IMPORT_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    query = InstitutionMigrationHistory.find(Eq(InstitutionMigrationHistory.tenant_id, tenant_id))
    total = await query.count()
    docs = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            MigrationHistoryItem(
                migration_id=d.migration_id,
                job_id=d.job_id,
                action=d.action,
                summary=d.summary,
                created_at=d.created_at,
            )
            for d in docs
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def issue_error_report(scope: AccessScope, user: User, job_id: str) -> ImportErrorReportRead:
    authorize(scope, Permission.IMPORT_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    job = await InstitutionImportJob.find_one(
        Eq(InstitutionImportJob.tenant_id, tenant_id),
        Eq(InstitutionImportJob.job_id, job_id),
    )
    if job is None:
        raise AppError(code="NOT_FOUND", message="Import job not found", status_code=404)
    expires = utcnow() + timedelta(minutes=15)
    token = None
    try:
        token, _ = await issue_import_error_token(tenant_id=str(tenant_id), user_id=str(user.id), job_id=job_id)
    except Exception:
        pass
    return ImportErrorReportRead(job_id=job_id, download_token=token, expires_at=expires)


async def download_error_report(scope: AccessScope, user: User, token: str) -> dict:
    authorize(scope, Permission.IMPORT_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    job_id = await resolve_import_error_token(tenant_id=str(tenant_id), token=token, user_id=str(user.id))
    errors = await InstitutionImportValidationError.find(
        Eq(InstitutionImportValidationError.tenant_id, tenant_id),
        Eq(InstitutionImportValidationError.job_id, job_id),
    ).sort("+row_number").to_list()
    return {
        "job_id": job_id,
        "errors": [
            {"row": e.row_number, "field": e.field, "code": e.error_code, "message": e.message}
            for e in errors
        ],
    }