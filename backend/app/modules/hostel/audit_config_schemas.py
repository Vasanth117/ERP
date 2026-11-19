"""Hostel audit and configuration API schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.hostel.config_models import HostelConfigLifecycle


class HostelAuditDashboard(BaseModel):
    total_entries: int
    infrastructure_changes: int
    allocation_changes: int
    resident_operations: int
    visitor_activity: int
    mess_billing: int
    leave_outpass: int
    maintenance_incidents: int
    integration_config: int


class HostelAuditSearch(BaseModel):
    module: str | None = None
    action: str | None = None
    actor_id: str | None = None
    resource_type: str | None = None
    hostel_code: str | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None


class HostelAuditLogRead(BaseModel):
    action: str
    module: str
    resource_type: str
    resource_id: str | None
    actor_id: str | None
    outcome: str
    metadata: dict[str, Any]
    created_at: datetime


class HostelConfigUpsert(BaseModel):
    policy_section: str
    hostel_code: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    effective_from: date | None = None
    effective_to: date | None = None
    change_reason: str | None = None


class HostelConfigRead(BaseModel):
    policy_section: str
    hostel_code: str | None
    version: int
    status: HostelConfigLifecycle
    payload: dict[str, Any]
    effective_from: date | None
    updated_at: datetime


class HostelConfigTransition(BaseModel):
    policy_section: str
    hostel_code: str | None = None
    action: str = Field(pattern="^(submit|approve|publish|suspend|archive)$")
    change_reason: str | None = None


class HostelPolicyDefinitionUpsert(BaseModel):
    policy_code: str
    title: str
    category: str
    description: str | None = None
    severity: str = "medium"
    hostel_codes: list[str] = Field(default_factory=list)
    rules: dict[str, Any] = Field(default_factory=dict)


class HostelPolicyRead(BaseModel):
    policy_code: str
    title: str
    category: str
    version: int
    status: HostelConfigLifecycle


class HostelPolicyApprovalInput(BaseModel):
    policy_code: str
    approve: bool
    comment: str | None = None