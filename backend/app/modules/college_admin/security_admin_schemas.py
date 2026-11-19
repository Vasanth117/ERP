"""Audit and security administration schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.college_admin.security_admin_models import SecurityIncidentStatus


class AuditLogSearch(BaseModel):
    actor_id: str | None = None
    module: str | None = None
    action_prefix: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    resource_type: str | None = None


class InstitutionAuditLogRead(BaseModel):
    id: str
    actor_id: str | None
    action: str
    module: str
    resource_type: str
    resource_id: str | None
    outcome: str
    entry_hash: str
    previous_entry_hash: str | None
    created_at: datetime


class SecurityEventRead(BaseModel):
    event_id: str
    code: str
    category: str
    severity: str
    title: str
    description: str
    status: SecurityIncidentStatus
    created_at: datetime


class LoginActivityRead(BaseModel):
    user_id: str | None
    email: str | None
    success: bool
    ip_address: str | None
    failure_reason: str | None
    created_at: datetime


class SecurityPolicyRead(BaseModel):
    policy_id: str
    max_failed_logins: int
    session_max_idle_minutes: int
    require_mfa_privileged: bool
    audit_retention_days: int
    block_self_approval: bool
    alert_on_privileged_access: bool
    updated_at: datetime


class SecurityPolicyUpdate(BaseModel):
    max_failed_logins: int | None = Field(default=None, ge=1)
    session_max_idle_minutes: int | None = Field(default=None, ge=5)
    require_mfa_privileged: bool | None = None
    audit_retention_days: int | None = Field(default=None, ge=30)
    block_self_approval: bool | None = None
    alert_on_privileged_access: bool | None = None


class SecurityReportRead(BaseModel):
    failed_logins_24h: int
    open_security_events: int
    privileged_operations_7d: int
    audit_chain_valid: bool


class AuditExportRead(BaseModel):
    export_id: str
    record_count: int
    download_token: str | None
    expires_at: datetime | None


class SessionRevokeRequest(BaseModel):
    user_id: str


class AccessReviewCreate(BaseModel):
    review_id: str
    subject_user_id: str
    decision: str
    notes: str | None = None


class IntegrityCheckRead(BaseModel):
    tenant_id: str
    entries_checked: int
    valid: bool
    broken_at: str | None