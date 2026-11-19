"""HR employee onboarding documents."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.hr.enums import HrOnboardingProcessStatus, HrOnboardingTaskStatus


class HrOnboardingChecklistTemplate(Document):
    tenant_id: PydanticObjectId
    template_code: str = Field(max_length=64)
    title: str = Field(max_length=200)
    employee_category: str = Field(max_length=64)
    tasks: list[dict[str, Any]] = Field(default_factory=list)
    is_active: bool = True
    version: int = 1
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_onboarding_checklist_templates"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("template_code", ASCENDING)],
                unique=True,
                name="unique_onboarding_template_code",
            ),
        ]


class HrOnboardingProcess(Document):
    tenant_id: PydanticObjectId
    process_code: str = Field(max_length=64)
    offer_id: PydanticObjectId
    application_id: PydanticObjectId
    candidate_id: PydanticObjectId
    employee_user_id: PydanticObjectId | None = None
    employee_record_id: PydanticObjectId | None = None
    template_id: PydanticObjectId
    department_id: PydanticObjectId
    designation: str = Field(max_length=200)
    reporting_manager_id: PydanticObjectId | None = None
    joining_date: date | None = None
    status: HrOnboardingProcessStatus = HrOnboardingProcessStatus.IN_PROGRESS
    mandatory_document_requirements: list[str] = Field(default_factory=list)
    completed_at: datetime | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_onboarding_processes"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("process_code", ASCENDING)],
                unique=True,
                name="unique_onboarding_process_code",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("offer_id", ASCENDING)],
                unique=True,
                name="unique_onboarding_per_offer",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("candidate_id", ASCENDING)],
                name="onboarding_by_candidate",
            ),
        ]


class HrOnboardingTask(Document):
    tenant_id: PydanticObjectId
    process_id: PydanticObjectId
    task_key: str = Field(max_length=64)
    title: str = Field(max_length=200)
    description: str = Field(max_length=2000, default="")
    responsible_role: str = Field(max_length=64)
    assigned_to_user_id: PydanticObjectId | None = None
    assigned_date: date | None = None
    due_date: date | None = None
    priority: str = Field(max_length=32, default="normal")
    status: HrOnboardingTaskStatus = HrOnboardingTaskStatus.ASSIGNED
    mandatory: bool = True
    completion_date: date | None = None
    remarks: str | None = Field(default=None, max_length=2000)
    document_ref: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_onboarding_tasks"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("process_id", ASCENDING), ("task_key", ASCENDING)],
                unique=True,
                name="unique_onboarding_task_key",
            ),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="onboarding_tasks_by_status"),
        ]


class HrOnboardingWaiver(Document):
    tenant_id: PydanticObjectId
    process_id: PydanticObjectId
    requirement_key: str = Field(max_length=128)
    reason: str = Field(max_length=2000)
    approved_by: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_onboarding_waivers"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("process_id", ASCENDING), ("requirement_key", ASCENDING)],
                unique=True,
                name="unique_onboarding_waiver",
            ),
        ]