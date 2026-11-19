"""Schemas for HR settings and policies."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.hr.enums import HrPolicyLifecycleStatus
from app.modules.hr.hr_settings_models import (
    HrConfigurablePolicy,
    HrGeneralSettings,
    HrPolicyAcknowledgement,
    HrPolicyApproval,
    HrPolicyCategory,
    HrPolicyVersion,
)


class GeneralSettingsUpsert(BaseModel):
    department_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    working_days: list[int] | None = None
    operating_hours: dict[str, str] | None = None
    calendar: dict[str, Any] | None = None
    employee_numbering: dict[str, Any] | None = None
    default_employee_categories: list[str] | None = None
    default_employment_types: list[str] | None = None
    profile_config: dict[str, Any] | None = None
    self_service_config: dict[str, Any] | None = None


class GeneralSettingsRead(BaseModel):
    id: str
    department_name: str | None
    contact_email: str | None
    contact_phone: str | None
    working_days: list[int]
    operating_hours: dict[str, str]
    calendar: dict[str, Any]
    employee_numbering: dict[str, Any]
    default_employee_categories: list[str]
    default_employment_types: list[str]
    profile_config: dict[str, Any]
    self_service_config: dict[str, Any]
    updated_at: datetime

    @classmethod
    def from_doc(cls, doc: HrGeneralSettings) -> "GeneralSettingsRead":
        return cls(
            id=str(doc.id),
            department_name=doc.department_name,
            contact_email=doc.contact_email,
            contact_phone=doc.contact_phone,
            working_days=doc.working_days,
            operating_hours=doc.operating_hours,
            calendar=doc.calendar,
            employee_numbering=doc.employee_numbering,
            default_employee_categories=doc.default_employee_categories,
            default_employment_types=doc.default_employment_types,
            profile_config=doc.profile_config,
            self_service_config=doc.self_service_config,
            updated_at=doc.updated_at,
        )


class PolicyCategoryUpsert(BaseModel):
    category_code: str = Field(max_length=64)
    title: str = Field(max_length=200)
    description: str | None = None
    sort_order: int = 0


class PolicyCategoryRead(BaseModel):
    id: str
    category_code: str
    title: str
    description: str | None
    sort_order: int
    is_active: bool

    @classmethod
    def from_doc(cls, doc: HrPolicyCategory) -> "PolicyCategoryRead":
        return cls(
            id=str(doc.id),
            category_code=doc.category_code,
            title=doc.title,
            description=doc.description,
            sort_order=doc.sort_order,
            is_active=doc.is_active,
        )


class PolicyUpsert(BaseModel):
    policy_code: str = Field(max_length=64)
    category_code: str = Field(max_length=64)
    title: str = Field(max_length=200)
    description: str | None = None
    requires_acknowledgement: bool = False
    settings: dict[str, Any] = Field(default_factory=dict)
    change_summary: str | None = None


class PolicyRead(BaseModel):
    id: str
    policy_code: str
    category_code: str
    title: str
    description: str | None
    status: HrPolicyLifecycleStatus
    current_version: int
    requires_acknowledgement: bool
    effective_from: date | None
    effective_to: date | None
    settings: dict[str, Any]
    published_at: datetime | None
    updated_at: datetime

    @classmethod
    def from_doc(cls, doc: HrConfigurablePolicy) -> "PolicyRead":
        return cls(
            id=str(doc.id),
            policy_code=doc.policy_code,
            category_code=doc.category_code,
            title=doc.title,
            description=doc.description,
            status=doc.status,
            current_version=doc.current_version,
            requires_acknowledgement=doc.requires_acknowledgement,
            effective_from=doc.effective_from,
            effective_to=doc.effective_to,
            settings=doc.settings,
            published_at=doc.published_at,
            updated_at=doc.updated_at,
        )


class PolicyTransition(BaseModel):
    action: str = Field(max_length=32)
    note: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None


class PolicyVersionRead(BaseModel):
    id: str
    policy_code: str
    version_number: int
    status: HrPolicyLifecycleStatus
    settings: dict[str, Any]
    change_summary: str | None
    effective_from: date | None
    effective_to: date | None
    created_at: datetime

    @classmethod
    def from_doc(cls, doc: HrPolicyVersion) -> "PolicyVersionRead":
        return cls(
            id=str(doc.id),
            policy_code=doc.policy_code,
            version_number=doc.version_number,
            status=doc.status,
            settings=doc.settings,
            change_summary=doc.change_summary,
            effective_from=doc.effective_from,
            effective_to=doc.effective_to,
            created_at=doc.created_at,
        )


class PolicyApprovalRead(BaseModel):
    action: str
    note: str | None
    actor_id: str
    created_at: datetime

    @classmethod
    def from_doc(cls, doc: HrPolicyApproval) -> "PolicyApprovalRead":
        return cls(
            action=doc.action,
            note=doc.note,
            actor_id=str(doc.actor_id),
            created_at=doc.created_at,
        )


class PolicyAcknowledgeRequest(BaseModel):
    viewed_only: bool = False


class PolicyAcknowledgementRead(BaseModel):
    policy_code: str
    version_number: int
    employee_user_id: str
    viewed_at: datetime | None
    acknowledged_at: datetime | None
    reminder_count: int

    @classmethod
    def from_doc(cls, doc: HrPolicyAcknowledgement) -> "PolicyAcknowledgementRead":
        return cls(
            policy_code=doc.policy_code,
            version_number=doc.version_number,
            employee_user_id=str(doc.employee_user_id),
            viewed_at=doc.viewed_at,
            acknowledged_at=doc.acknowledged_at,
            reminder_count=doc.reminder_count,
        )