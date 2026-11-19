"""HR settings, configurable policies and acknowledgements."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.hr.enums import HrPolicyLifecycleStatus


class HrGeneralSettings(Document):
    tenant_id: PydanticObjectId
    department_name: str | None = Field(default=None, max_length=200)
    contact_email: str | None = None
    contact_phone: str | None = None
    working_days: list[int] = Field(default_factory=lambda: [1, 2, 3, 4, 5])
    operating_hours: dict[str, str] = Field(default_factory=dict)
    calendar: dict[str, Any] = Field(default_factory=dict)
    employee_numbering: dict[str, Any] = Field(default_factory=dict)
    default_employee_categories: list[str] = Field(default_factory=list)
    default_employment_types: list[str] = Field(default_factory=list)
    profile_config: dict[str, Any] = Field(default_factory=dict)
    self_service_config: dict[str, Any] = Field(default_factory=dict)
    actor_id: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_general_settings"
        indexes = [IndexModel([("tenant_id", ASCENDING)], unique=True, name="unique_hr_general_settings")]


class HrPolicyCategory(Document):
    tenant_id: PydanticObjectId
    category_code: str = Field(max_length=64)
    title: str = Field(max_length=200)
    description: str | None = None
    sort_order: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_policy_categories"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("category_code", ASCENDING)], unique=True, name="unique_hr_policy_category"),
        ]


class HrConfigurablePolicy(Document):
    """Versioned HR policy registry (distinct from legacy college_admin HrPolicy)."""

    tenant_id: PydanticObjectId
    policy_code: str = Field(max_length=64)
    category_code: str = Field(max_length=64)
    title: str = Field(max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    status: HrPolicyLifecycleStatus = HrPolicyLifecycleStatus.DRAFT
    current_version: int = 1
    requires_acknowledgement: bool = False
    effective_from: date | None = None
    effective_to: date | None = None
    settings: dict[str, Any] = Field(default_factory=dict)
    actor_id: PydanticObjectId | None = None
    approved_by: PydanticObjectId | None = None
    published_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_staff_policy_registry"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("policy_code", ASCENDING)], unique=True, name="unique_hr_staff_policy"),
            IndexModel([("tenant_id", ASCENDING), ("category_code", ASCENDING)], name="hr_policies_by_category"),
        ]


class HrPolicyVersion(Document):
    tenant_id: PydanticObjectId
    policy_id: PydanticObjectId
    policy_code: str = Field(max_length=64)
    version_number: int
    status: HrPolicyLifecycleStatus
    settings: dict[str, Any] = Field(default_factory=dict)
    change_summary: str | None = Field(default=None, max_length=2000)
    effective_from: date | None = None
    effective_to: date | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_policy_versions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("policy_id", ASCENDING), ("version_number", ASCENDING)],
                unique=True,
                name="unique_hr_policy_version",
            ),
        ]


class HrPolicyApproval(Document):
    tenant_id: PydanticObjectId
    policy_id: PydanticObjectId
    version_number: int
    action: str = Field(max_length=32)
    note: str | None = Field(default=None, max_length=2000)
    actor_id: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_policy_approvals"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("policy_id", ASCENDING), ("created_at", DESCENDING)], name="hr_policy_approval_history"),
        ]


class HrPolicyAcknowledgement(Document):
    tenant_id: PydanticObjectId
    policy_id: PydanticObjectId
    policy_code: str = Field(max_length=64)
    version_number: int
    employee_user_id: PydanticObjectId
    viewed_at: datetime | None = None
    acknowledged_at: datetime | None = None
    reminder_count: int = 0
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_policy_acknowledgements"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("policy_id", ASCENDING), ("employee_user_id", ASCENDING), ("version_number", ASCENDING)],
                unique=True,
                name="unique_policy_ack",
            ),
        ]