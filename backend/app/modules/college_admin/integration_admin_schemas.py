"""Institution integration administration schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.college_admin.integration_admin_models import InstitutionIntegrationStatus


class IntegrationRegisterRequest(BaseModel):
    integration_key: str
    provider_code: str
    title: str


class IntegrationRead(BaseModel):
    integration_key: str
    provider_code: str
    title: str
    version: int
    status: InstitutionIntegrationStatus
    configuration_id: str | None


class IntegrationConfigUpdate(BaseModel):
    connection_url: str | None = None
    settings: dict[str, Any] | None = None
    credential_refs: dict[str, str] = Field(default_factory=dict)
    enabled: bool | None = None


class IntegrationHealthRead(BaseModel):
    integration_key: str
    status: str
    last_check_at: datetime | None
    detail: str | None


class SyncHistoryRead(BaseModel):
    sync_id: str
    status: str
    detail: str | None
    started_at: datetime
    finished_at: datetime | None


class WebhookEndpointUpsert(BaseModel):
    endpoint_id: str
    integration_key: str
    path_suffix: str
    signing_secret_ref: str
    replay_window_seconds: int = 300


class WebhookEndpointRead(BaseModel):
    endpoint_id: str
    integration_key: str
    path_suffix: str
    signing_secret_ref: str
    enabled: bool


class WebhookVerifyRequest(BaseModel):
    timestamp: str
    signature: str
    body_base64: str
    endpoint_id: str
    idempotency_key: str | None = None


class CredentialRotateRequest(BaseModel):
    credential_key: str
    secret_ref: str