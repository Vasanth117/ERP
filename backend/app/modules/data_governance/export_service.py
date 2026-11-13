"""Tenant data export workflow."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.models import AuditLog
from app.modules.auth.models import User
from app.modules.configuration.models import TenantBranding, TenantConfiguration
from app.modules.data_governance.download_tokens import (
    build_download_authorization,
    default_download_expiry,
    hash_download_token,
    issue_raw_download_token,
    verify_download_authorization,
)
from app.modules.data_governance.enums import (
    ALLOWED_EXPORT_MODULES,
    ExportFormat,
    ExportJobStatus,
    ExportRequestStatus,
)
from app.modules.data_governance.models import (
    TenantExportArtifact,
    TenantExportDownload,
    TenantExportJob,
    TenantExportRequest,
)
from app.modules.data_governance.schemas import (
    ExportArtifactRead,
    ExportDownloadIssueResponse,
    ExportJobRead,
    ExportRequestCreate,
    ExportRequestRead,
    ExportReviewRequest,
)
from app.modules.data_governance.storage import read_artifact_bytes, storage_key_for, write_json_export
from app.modules.platform_ops.enums import BackgroundJobStatus
from app.modules.platform_ops.job_registry import ensure_job_registry, record_job_failure, update_job_registry_status
from app.modules.platform_security.audit import record_platform_audit
from app.modules.tenants.models import Department, Tenant
from app.repositories.tenant_repository import TenantRepository

_tenant_repo = TenantRepository()


def _validate_export_scope(payload: ExportRequestCreate) -> None:
    unknown = set(payload.module_scopes) - ALLOWED_EXPORT_MODULES
    if unknown:
        raise AppError(
            code="EXPORT_SCOPE_INVALID",
            message=f"Unknown export modules: {', '.join(sorted(unknown))}",
            status_code=400,
        )


async def _load_tenant(tenant_id: PydanticObjectId) -> Tenant:
    tenant = await _tenant_repo.get_tenant(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)
    return tenant


async def create_export_request(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    payload: ExportRequestCreate,
) -> ExportRequestRead:
    authorize(scope, Permission.PLATFORM_EXPORT_MANAGE)
    await _load_tenant(tenant_id)
    _validate_export_scope(payload)
    if payload.idempotency_key:
        existing = await TenantExportRequest.find_one(
            Eq(TenantExportRequest.tenant_id, tenant_id),
            Eq(TenantExportRequest.idempotency_key, payload.idempotency_key),
        )
        if existing is not None:
            return ExportRequestRead.from_document(existing)

    doc = TenantExportRequest(
        tenant_id=tenant_id,
        requested_by=scope.user_id,
        formats=payload.formats,
        module_scopes=list(payload.module_scopes),
        include_document_metadata=payload.include_document_metadata,
        include_sensitive=payload.include_sensitive,
        idempotency_key=payload.idempotency_key,
    )
    await doc.insert()
    await record_platform_audit(
        actor_id=scope.user_id,
        action="export.request.created",
        module="data_governance",
        resource_type="tenant_export_request",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        metadata={"modules": doc.module_scopes},
    )
    return ExportRequestRead.from_document(doc)


async def list_export_requests(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    pagination: Pagination,
) -> Page[ExportRequestRead]:
    authorize(scope, Permission.PLATFORM_EXPORT_READ)
    await _load_tenant(tenant_id)
    query = TenantExportRequest.find(Eq(TenantExportRequest.tenant_id, tenant_id)).sort("-created_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    items = [ExportRequestRead.from_document(r) for r in rows]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def get_export_request(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    request_id: PydanticObjectId,
) -> ExportRequestRead:
    authorize(scope, Permission.PLATFORM_EXPORT_READ)
    doc = await TenantExportRequest.get(request_id)
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Export request not found", status_code=404)
    return ExportRequestRead.from_document(doc)


async def review_export_request(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    request_id: PydanticObjectId,
    payload: ExportReviewRequest,
) -> ExportRequestRead:
    authorize(scope, Permission.PLATFORM_EXPORT_MANAGE)
    doc = await TenantExportRequest.get(request_id)
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Export request not found", status_code=404)
    if doc.status != ExportRequestStatus.PENDING_REVIEW:
        raise AppError(code="CONFLICT", message="Export request is not pending review", status_code=409)
    if payload.approved:
        if doc.include_sensitive:
            authorize(scope, Permission.PLATFORM_OFFBOARDING_MANAGE)
        doc.status = ExportRequestStatus.APPROVED
    else:
        doc.status = ExportRequestStatus.REJECTED
    doc.review_note = payload.note
    doc.reviewed_by = scope.user_id
    doc.reviewed_at = utcnow()
    doc.updated_at = utcnow()
    await doc.save()
    await record_platform_audit(
        actor_id=scope.user_id,
        action="export.request.reviewed",
        module="data_governance",
        resource_type="tenant_export_request",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        metadata={"approved": payload.approved},
    )
    return ExportRequestRead.from_document(doc)


async def _build_export_payload(tenant_id: PydanticObjectId, request: TenantExportRequest) -> dict:
    tenant = await _load_tenant(tenant_id)
    payload: dict = {"tenant_id": str(tenant_id), "tenant_code": tenant.code, "modules": {}}
    scopes = set(request.module_scopes)
    if "tenant_registry" in scopes:
        payload["modules"]["tenant_registry"] = {
            "code": tenant.code,
            "name": tenant.name,
            "lifecycle_status": tenant.lifecycle_status.value,
            "created_at": tenant.created_at.isoformat(),
        }
    if "configuration" in scopes:
        configs = await TenantConfiguration.find(Eq(TenantConfiguration.tenant_id, tenant_id)).to_list()
        branding = await TenantBranding.find_one(Eq(TenantBranding.tenant_id, tenant_id))
        payload["modules"]["configuration"] = {
            "settings": [c.settings for c in configs],
            "branding": branding.model_dump() if branding else None,
        }
    if "users_metadata" in scopes:
        users = await User.find(Eq(User.tenant_id, tenant_id)).to_list()
        payload["modules"]["users_metadata"] = [
            {"id": str(u.id), "email": u.email, "role": u.role.value, "active": u.is_active}
            for u in users
        ]
    if "departments" in scopes:
        depts = await Department.find(Eq(Department.tenant_id, tenant_id)).to_list()
        payload["modules"]["departments"] = [{"id": str(d.id), "name": d.name, "code": d.code} for d in depts]
    if "audit_logs" in scopes:
        logs = await AuditLog.find(Eq(AuditLog.tenant_id, tenant_id)).sort("-created_at").limit(500).to_list()
        payload["modules"]["audit_logs"] = [
            {"action": log.action, "actor_id": str(log.actor_id), "created_at": log.created_at.isoformat()}
            for log in logs
        ]
    if "documents_metadata" in scopes and request.include_document_metadata:
        payload["modules"]["documents_metadata"] = []
    return payload


async def start_export_job(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    request_id: PydanticObjectId,
) -> ExportJobRead:
    authorize(scope, Permission.PLATFORM_EXPORT_MANAGE)
    request = await TenantExportRequest.get(request_id)
    if request is None or request.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Export request not found", status_code=404)
    if request.status != ExportRequestStatus.APPROVED:
        raise AppError(code="CONFLICT", message="Export must be approved before starting", status_code=409)

    job = await TenantExportJob.find_one(Eq(TenantExportJob.request_id, request_id))
    if job is None:
        job = TenantExportJob(tenant_id=tenant_id, request_id=request_id)
        await job.insert()
    else:
        if job.status == ExportJobStatus.SUCCEEDED:
            return ExportJobRead.from_document(job)

    request.status = ExportRequestStatus.RUNNING
    request.updated_at = utcnow()
    await request.save()

    job.status = ExportJobStatus.RUNNING
    job.started_at = utcnow()
    job.progress_percent = 10
    await job.save()

    registry = await ensure_job_registry(
        job_type="tenant.data_export",
        job_key=str(job.id),
        safe_to_retry=True,
        summary=f"Data export for tenant {tenant_id}",
        tenant_id=tenant_id,
        idempotency_key=str(request_id),
    )
    registry.status = BackgroundJobStatus.RUNNING
    await registry.save()

    try:
        export_body = await _build_export_payload(tenant_id, request)
        job.progress_percent = 60
        await job.save()
        fmt = ExportFormat.JSON
        key = storage_key_for(str(tenant_id), str(job.id), fmt.value)
        size, checksum = write_json_export(key, export_body)
        artifact = TenantExportArtifact(
            tenant_id=tenant_id,
            job_id=job.id,
            format=fmt,
            storage_key=key,
            byte_size=size,
            checksum_sha256=checksum,
            validated=True,
        )
        await artifact.insert()
        job.progress_percent = 100
        job.status = ExportJobStatus.SUCCEEDED
        job.completed_at = utcnow()
        await job.save()
        request.status = ExportRequestStatus.COMPLETED
        request.updated_at = utcnow()
        await request.save()
        await update_job_registry_status(
            job_type="tenant.data_export",
            job_key=str(job.id),
            status=BackgroundJobStatus.SUCCEEDED,
        )
    except Exception as exc:  # noqa: BLE001 — export boundary
        job.status = ExportJobStatus.FAILED
        job.last_error = str(exc)[:500]
        job.attempt_count += 1
        await job.save()
        request.status = ExportRequestStatus.FAILED
        request.updated_at = utcnow()
        await request.save()
        await record_job_failure(
            registry=registry,
            error_code="EXPORT_FAILED",
            error_message=str(exc),
        )
        raise AppError(code="EXPORT_FAILED", message="Export job failed", status_code=500) from exc

    await record_platform_audit(
        actor_id=scope.user_id,
        action="export.job.completed",
        module="data_governance",
        resource_type="tenant_export_job",
        resource_id=str(job.id),
        tenant_id=tenant_id,
    )
    return ExportJobRead.from_document(job)


async def get_export_progress(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    request_id: PydanticObjectId,
) -> ExportJobRead:
    authorize(scope, Permission.PLATFORM_EXPORT_READ)
    job = await TenantExportJob.find_one(Eq(TenantExportJob.request_id, request_id))
    if job is None or job.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Export job not found", status_code=404)
    return ExportJobRead.from_document(job)


async def retry_export_job(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    request_id: PydanticObjectId,
) -> ExportJobRead:
    authorize(scope, Permission.PLATFORM_EXPORT_MANAGE)
    request = await TenantExportRequest.get(request_id)
    if request is None or request.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Export request not found", status_code=404)
    if request.status not in {ExportRequestStatus.FAILED, ExportRequestStatus.COMPLETED}:
        request.status = ExportRequestStatus.APPROVED
        await request.save()
    return await start_export_job(scope, tenant_id, request_id)


async def get_export_artifacts(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    request_id: PydanticObjectId,
) -> list[ExportArtifactRead]:
    authorize(scope, Permission.PLATFORM_EXPORT_READ)
    job = await TenantExportJob.find_one(Eq(TenantExportJob.request_id, request_id))
    if job is None or job.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Export job not found", status_code=404)
    artifacts = await TenantExportArtifact.find(Eq(TenantExportArtifact.job_id, job.id)).to_list()
    return [ExportArtifactRead.from_document(a) for a in artifacts]


async def issue_download_access(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    artifact_id: PydanticObjectId,
) -> ExportDownloadIssueResponse:
    authorize(scope, Permission.PLATFORM_EXPORT_READ)
    artifact = await TenantExportArtifact.get(artifact_id)
    if artifact is None or artifact.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Artifact not found", status_code=404)
    if not artifact.validated:
        raise AppError(code="CONFLICT", message="Export not validated", status_code=409)

    raw = issue_raw_download_token()
    expires = default_download_expiry()
    signature = build_download_authorization(
        artifact_id=str(artifact.id),
        tenant_id=str(tenant_id),
        user_id=str(scope.user_id),
        expires_at=expires,
        raw_token=raw,
    )
    download = TenantExportDownload(
        tenant_id=tenant_id,
        artifact_id=artifact.id,
        issued_to=scope.user_id,
        token_hash=hash_download_token(raw),
        expires_at=expires,
    )
    await download.insert()
    await record_platform_audit(
        actor_id=scope.user_id,
        action="export.download.issued",
        module="data_governance",
        resource_type="tenant_export_download",
        resource_id=str(download.id),
        tenant_id=tenant_id,
    )
    return ExportDownloadIssueResponse(
        download_id=str(download.id),
        token=raw,
        signature=signature,
        expires_at=expires,
        artifact_id=str(artifact.id),
    )


async def stream_authorized_download(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    artifact_id: PydanticObjectId,
    raw_token: str,
    signature: str,
) -> tuple[bytes, str]:
    authorize(scope, Permission.PLATFORM_EXPORT_READ)
    artifact = await TenantExportArtifact.get(artifact_id)
    if artifact is None or artifact.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Artifact not found", status_code=404)

    token_hash = hash_download_token(raw_token)
    download = await TenantExportDownload.find_one(
        Eq(TenantExportDownload.token_hash, token_hash),
        Eq(TenantExportDownload.artifact_id, artifact.id),
    )
    if download is None or download.revoked:
        raise AppError(code="DOWNLOAD_UNAUTHORIZED", message="Invalid download token", status_code=403)
    if download.issued_to != scope.user_id:
        raise AppError(code="FORBIDDEN", message="Download not issued to this operator", status_code=403)
    if download.download_count >= download.max_downloads:
        raise AppError(code="DOWNLOAD_LIMIT", message="Download limit exceeded", status_code=403)

    verify_download_authorization(
        artifact_id=str(artifact.id),
        tenant_id=str(tenant_id),
        user_id=str(scope.user_id),
        expires_at=download.expires_at,
        raw_token=raw_token,
        signature=signature,
    )

    data = read_artifact_bytes(artifact.storage_key)
    download.download_count += 1
    download.last_access_at = utcnow()
    await download.save()
    await record_platform_audit(
        actor_id=scope.user_id,
        action="export.download.accessed",
        module="data_governance",
        resource_type="tenant_export_artifact",
        resource_id=str(artifact.id),
        tenant_id=tenant_id,
    )
    filename = f"tenant-{tenant_id}-export.{artifact.format.value}"
    return data, filename
