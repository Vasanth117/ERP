"""Examination integration, security and audit services."""

import time
from typing import Any
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.integrations.enums import IntegrationScope
from app.modules.integrations.models import IntegrationConfiguration, IntegrationHealth
from app.modules.examinations.exam_cell_policy import (
    authorize_examination_cell_audit_read,
    authorize_examination_cell_integration_manage,
    authorize_examination_cell_integration_read,
    authorize_examination_cell_security_manage,
    authorize_examination_cell_security_read,
    require_examination_cell_tenant,
)
from app.modules.examinations.exam_cell_redaction import redact_mapping
from app.modules.examinations.exam_cell_security_enums import (
    ExamAccessReviewStatus,
    ExamIntegrationSyncStatus,
    ExamIntegrationTarget,
)
from app.modules.examinations.exam_cell_security_models import (
    ExamAccessReviewRecord,
    ExamAuditLog,
    ExamIntegrationConfig,
    ExamIntegrationFailure,
    ExamIntegrationSyncLog,
    ExamSecurityEvent,
)
from app.modules.examinations.exam_cell_security_recorder import record_exam_security_event
from app.modules.examinations.exam_cell_security_schemas import (
    DEFAULT_INTEGRATION_TARGETS,
    ExamAccessReviewComplete,
    ExamAccessReviewCreate,
    ExamAccessReviewRead,
    ExamAuditLogRead,
    ExamAuditSearch,
    ExamIntegrationConfigRead,
    ExamIntegrationConfigUpdate,
    ExamIntegrationFailureRead,
    ExamIntegrationHealthReport,
    ExamIntegrationSyncLogRead,
    ExamIntegrationSyncRequest,
    ExamSecurityEventRead,
)
from app.modules.examinations.exam_cell_security_enums import ExamSecurityEventType


def _config_id() -> str:
    return f"eic_{uuid4().hex[:12]}"


def _sync_id() -> str:
    return f"esync_{uuid4().hex[:12]}"


def _failure_id() -> str:
    return f"efail_{uuid4().hex[:12]}"


def _review_id() -> str:
    return f"ear_{uuid4().hex[:12]}"


async def ensure_integration_configs(tenant_id: PydanticObjectId) -> None:
    for target in DEFAULT_INTEGRATION_TARGETS:
        existing = await ExamIntegrationConfig.find_one(
            Eq(ExamIntegrationConfig.tenant_id, tenant_id),
            Eq(ExamIntegrationConfig.integration_target, target),
        )
        if existing is None:
            await ExamIntegrationConfig(
                tenant_id=tenant_id,
                config_id=_config_id(),
                integration_target=target,
                enabled=True,
            ).insert()


async def list_integration_configs(scope: AccessScope) -> list[ExamIntegrationConfigRead]:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_integration_read(scope)
    await ensure_integration_configs(tenant_id)
    rows = await ExamIntegrationConfig.find(Eq(ExamIntegrationConfig.tenant_id, tenant_id)).to_list()
    return [ExamIntegrationConfigRead.from_doc(r) for r in rows]


async def update_integration_config(
    scope: AccessScope,
    actor: User,
    integration_target: str,
    payload: ExamIntegrationConfigUpdate,
) -> ExamIntegrationConfigRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_integration_manage(scope)
    doc = await ExamIntegrationConfig.find_one(
        Eq(ExamIntegrationConfig.tenant_id, tenant_id),
        Eq(ExamIntegrationConfig.integration_target, integration_target),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Integration config not found", status_code=404)
    if payload.enabled is not None:
        doc.enabled = payload.enabled
    if payload.platform_provider_code is not None:
        doc.platform_provider_code = payload.platform_provider_code
        platform = await IntegrationConfiguration.find_one(
            Eq(IntegrationConfiguration.provider_code, payload.platform_provider_code),
            Eq(IntegrationConfiguration.scope, IntegrationScope.TENANT),
            Eq(IntegrationConfiguration.tenant_id, tenant_id),
        )
        if platform is None:
            platform = await IntegrationConfiguration.find_one(
                Eq(IntegrationConfiguration.provider_code, payload.platform_provider_code),
                Eq(IntegrationConfiguration.scope, IntegrationScope.GLOBAL),
            )
        doc.platform_configuration_id = platform.id if platform else None
    if payload.webhook_enabled is not None:
        doc.webhook_enabled = payload.webhook_enabled
    if payload.webhook_secret_ref is not None:
        doc.webhook_secret_ref = payload.webhook_secret_ref
    if payload.settings is not None:
        doc.settings = payload.settings
    doc.updated_by = actor.id
    doc.updated_at = utcnow()
    await doc.save()

    from app.modules.examinations.exam_cell_audit import record_exam_audit as write_audit

    await write_audit(
        tenant_id,
        actor_id=actor.id,
        action="exam.integration_config.updated",
        resource_type="exam_integration_config",
        resource_id=doc.config_id,
        after_state={"integration_target": integration_target, "enabled": doc.enabled},
        reason="Integration configuration change",
    )
    return ExamIntegrationConfigRead.from_doc(doc)


async def run_integration_sync(
    scope: AccessScope,
    actor: User,
    integration_target: str,
    payload: ExamIntegrationSyncRequest,
) -> ExamIntegrationSyncLogRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_integration_manage(scope)
    doc = await ExamIntegrationConfig.find_one(
        Eq(ExamIntegrationConfig.tenant_id, tenant_id),
        Eq(ExamIntegrationConfig.integration_target, integration_target),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Integration config not found", status_code=404)
    if not doc.enabled:
        raise AppError(code="INTEGRATION_DISABLED", message="Integration target is disabled", status_code=409)

    dup = await ExamIntegrationSyncLog.find_one(
        Eq(ExamIntegrationSyncLog.tenant_id, tenant_id),
        Eq(ExamIntegrationSyncLog.idempotency_key, payload.idempotency_key),
    )
    if dup:
        return ExamIntegrationSyncLogRead.from_doc(dup)

    started = time.perf_counter()
    correlation_id = get_request_id()
    status = ExamIntegrationSyncStatus.SUCCESS
    request_payload = redact_mapping({"integration_target": integration_target, "tenant_id": str(tenant_id)})
    response_payload: dict[str, Any] = {"ok": True}

    try:
        if doc.platform_configuration_id:
            health = await IntegrationHealth.find_one(
                Eq(IntegrationHealth.configuration_id, doc.platform_configuration_id)
            )
            if health and str(health.status) in {"failed", "degraded", "IntegrationOperationalStatus.FAILED", "IntegrationOperationalStatus.DEGRADED"}:
                status = ExamIntegrationSyncStatus.PARTIAL
                response_payload = {"ok": False, "health_status": str(health.status)}
        _probe_target(integration_target)
    except Exception as exc:
        status = ExamIntegrationSyncStatus.FAILURE
        response_payload = {"ok": False, "error": str(exc)[:200]}
        await ExamIntegrationFailure(
            tenant_id=tenant_id,
            failure_id=_failure_id(),
            config_id=doc.config_id,
            integration_target=integration_target,
            error_code="SYNC_FAILED",
            error_message=str(exc)[:500],
        ).insert()

    elapsed = int((time.perf_counter() - started) * 1000)
    log = ExamIntegrationSyncLog(
        tenant_id=tenant_id,
        sync_id=_sync_id(),
        config_id=doc.config_id,
        integration_target=integration_target,
        idempotency_key=payload.idempotency_key,
        status=status.value,
        request_redacted=request_payload,
        response_redacted=redact_mapping(response_payload),
        actor_id=actor.id,
        correlation_id=correlation_id,
        duration_ms=elapsed,
    )
    await log.insert()
    from app.modules.examinations.exam_cell_audit import record_exam_audit as write_audit

    await write_audit(
        tenant_id,
        actor_id=actor.id,
        action="exam.integration.sync",
        resource_type="exam_integration_config",
        resource_id=doc.config_id,
        metadata={"sync_id": log.sync_id, "status": status.value},
    )
    return ExamIntegrationSyncLogRead.from_doc(log)


def _probe_target(target: str) -> None:
    """Lightweight validation that the target key is recognised."""
    if target not in {t.value for t in ExamIntegrationTarget}:
        raise AppError(code="VALIDATION_ERROR", message="Unknown integration target", status_code=422)


async def retry_integration_failure(scope: AccessScope, actor: User, failure_id: str) -> ExamIntegrationFailureRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_integration_manage(scope)
    row = await ExamIntegrationFailure.find_one(
        Eq(ExamIntegrationFailure.tenant_id, tenant_id),
        Eq(ExamIntegrationFailure.failure_id, failure_id),
    )
    if row is None:
        raise AppError(code="NOT_FOUND", message="Failure record not found", status_code=404)
    if row.recovered:
        return ExamIntegrationFailureRead.from_doc(row)
    row.retry_count += 1
    row.updated_at = utcnow()
    row.recovered = True
    row.recovered_at = utcnow()
    await row.save()
    await run_integration_sync(
        scope,
        actor,
        row.integration_target,
        ExamIntegrationSyncRequest(idempotency_key=f"retry:{failure_id}:{row.retry_count}"),
    )
    return ExamIntegrationFailureRead.from_doc(row)


async def integration_health_report(scope: AccessScope) -> ExamIntegrationHealthReport:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_integration_read(scope)
    await ensure_integration_configs(tenant_id)
    configs = await ExamIntegrationConfig.find(Eq(ExamIntegrationConfig.tenant_id, tenant_id)).to_list()
    failures = await ExamIntegrationFailure.find(
        Eq(ExamIntegrationFailure.tenant_id, tenant_id),
        Eq(ExamIntegrationFailure.recovered, False),
    ).to_list()
    last_sync = (
        await ExamIntegrationSyncLog.find(Eq(ExamIntegrationSyncLog.tenant_id, tenant_id))
        .sort("-created_at")
        .first_or_none()
    )
    targets = []
    for cfg in configs:
        state = "enabled" if cfg.enabled else "disabled"
        if cfg.platform_configuration_id:
            health = await IntegrationHealth.find_one(Eq(IntegrationHealth.configuration_id, cfg.platform_configuration_id))
            if health:
                state = health.status.value
        targets.append({"integration_target": cfg.integration_target, "status": state})
    return ExamIntegrationHealthReport(
        targets_total=len(configs),
        targets_enabled=sum(1 for c in configs if c.enabled),
        open_failures=len(failures),
        last_sync_at=last_sync.created_at if last_sync else None,
        targets=targets,
    )


async def search_exam_audit(
    scope: AccessScope,
    pagination: Pagination,
    filters: ExamAuditSearch,
) -> Page[ExamAuditLogRead]:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_audit_read(scope)
    query: dict[str, Any] = {"tenant_id": tenant_id}
    if filters.resource_type:
        query["resource_type"] = filters.resource_type.strip()
    if filters.resource_id:
        query["resource_id"] = filters.resource_id.strip()
    if filters.actor_id:
        query["actor_id"] = to_object_id(filters.actor_id, "actor_id")
    if filters.exam_session_id:
        query["exam_session_id"] = to_object_id(filters.exam_session_id, "exam_session_id")
    rows = await ExamAuditLog.find(query).sort("-created_at").to_list()
    if filters.action_prefix:
        prefix = filters.action_prefix.strip()
        rows = [r for r in rows if r.action.startswith(prefix)]
    total = len(rows)
    page = rows[pagination.offset : pagination.offset + pagination.limit]
    return Page(
        items=[ExamAuditLogRead.from_doc(r) for r in page],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def list_security_events(scope: AccessScope, pagination: Pagination) -> Page[ExamSecurityEventRead]:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_security_read(scope)
    query = ExamSecurityEvent.find(Eq(ExamSecurityEvent.tenant_id, tenant_id))
    total = await query.count()
    rows = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[ExamSecurityEventRead.from_doc(r) for r in rows],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def create_access_review(scope: AccessScope, actor: User, payload: ExamAccessReviewCreate) -> ExamAccessReviewRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_security_manage(scope)
    subject = to_object_id(payload.subject_user_id, "subject_user_id")
    user = await User.find_one(Eq(User.id, subject))
    if user is None or user.tenant_id != tenant_id:
        raise AppError(code="VALIDATION_ERROR", message="Subject user not in tenant", status_code=422)
    doc = ExamAccessReviewRecord(
        tenant_id=tenant_id,
        review_id=_review_id(),
        subject_user_id=subject,
        permission_codes=payload.permission_codes,
        status=ExamAccessReviewStatus.OPEN.value,
        findings=payload.findings,
        created_by=actor.id,
    )
    await doc.insert()
    from app.modules.examinations.exam_cell_audit import record_exam_audit as write_audit

    await write_audit(
        tenant_id,
        actor_id=actor.id,
        action="exam.access_review.created",
        resource_type="exam_access_review",
        resource_id=doc.review_id,
        after_state={"subject_user_id": str(subject), "permissions": payload.permission_codes},
    )
    return ExamAccessReviewRead.from_doc(doc)


async def complete_access_review(
    scope: AccessScope,
    actor: User,
    review_id: str,
    payload: ExamAccessReviewComplete,
) -> ExamAccessReviewRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_security_manage(scope)
    doc = await ExamAccessReviewRecord.find_one(
        Eq(ExamAccessReviewRecord.tenant_id, tenant_id),
        Eq(ExamAccessReviewRecord.review_id, review_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Access review not found", status_code=404)
    if doc.status != ExamAccessReviewStatus.OPEN.value:
        raise AppError(code="INVALID_STATE", message="Review already completed", status_code=409)
    doc.status = ExamAccessReviewStatus.COMPLETED.value
    doc.findings = payload.findings
    doc.reviewer_id = actor.id
    doc.completed_at = utcnow()
    doc.updated_at = utcnow()
    await doc.save()
    from app.modules.examinations.exam_cell_audit import record_exam_audit as write_audit

    await write_audit(
        tenant_id,
        actor_id=actor.id,
        action="exam.access_review.completed",
        resource_type="exam_access_review",
        resource_id=review_id,
        reason=payload.findings,
    )
    return ExamAccessReviewRead.from_doc(doc)


async def handle_integration_webhook(
    scope: AccessScope,
    actor: User,
    integration_target: str,
    body: ExamIntegrationSyncRequest,
) -> ExamIntegrationSyncLogRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_integration_manage(scope)
    config = await ExamIntegrationConfig.find_one(
        Eq(ExamIntegrationConfig.tenant_id, tenant_id),
        Eq(ExamIntegrationConfig.integration_target, integration_target),
    )
    if config is None or not config.enabled or not config.webhook_enabled:
        raise AppError(code="FORBIDDEN", message="Webhook not enabled for target", status_code=403)
    if not config.webhook_secret_ref:
        raise AppError(code="VALIDATION_ERROR", message="Webhook secret reference not configured", status_code=422)
    return await run_integration_sync(scope, actor, integration_target, body)


async def record_unauthorized_access(
    scope: AccessScope,
    *,
    actor_id: PydanticObjectId | None,
    resource_type: str,
    resource_id: str | None,
    detail: str,
) -> None:
    tenant_id = require_examination_cell_tenant(scope)
    await record_exam_security_event(
        tenant_id,
        event_type=ExamSecurityEventType.UNAUTHORIZED_ACCESS,
        actor_id=actor_id,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail,
        request_id=get_request_id(),
    )