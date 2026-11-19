"""Resignation, notice period, and offboarding."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.hr.enums import HrOffboardingProcessStatus, HrOffboardingTaskStatus, HrResignationStatus


class HrResignationRequest(Document):
    tenant_id: PydanticObjectId
    resignation_code: str = Field(max_length=64)
    employee_user_id: PydanticObjectId
    submitted_at: datetime = Field(default_factory=utcnow)
    proposed_last_working_date: date
    reason: str = Field(max_length=2000)
    employee_remarks: str | None = Field(default=None, max_length=2000)
    document_refs: list[str] = Field(default_factory=list)
    manager_review: str | None = Field(default=None, max_length=2000)
    hr_review: str | None = Field(default=None, max_length=2000)
    management_decision: str | None = Field(default=None, max_length=2000)
    status: HrResignationStatus = HrResignationStatus.SUBMITTED
    requested_by: PydanticObjectId
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_resignation_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("resignation_code", ASCENDING)],
                unique=True,
                name="unique_resignation_code",
            ),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="hr_resignations_by_status"),
        ]


class HrNoticePeriodRecord(Document):
    tenant_id: PydanticObjectId
    resignation_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    notice_start_date: date
    required_notice_days: int = Field(ge=0, default=30)
    expected_last_working_date: date
    actual_last_working_date: date | None = None
    waiver_reason: str | None = Field(default=None, max_length=2000)
    waiver_approved_by: PydanticObjectId | None = None
    early_release: bool = False
    extension_days: int = Field(ge=0, default=0)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_notice_period_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("resignation_id", ASCENDING)], unique=True, name="unique_notice_per_resignation"),
        ]


class HrOffboardingChecklistTemplate(Document):
    tenant_id: PydanticObjectId
    template_code: str = Field(max_length=64)
    title: str = Field(max_length=200)
    tasks: list[dict[str, Any]] = Field(default_factory=list)
    is_active: bool = True
    version: int = 1
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_offboarding_checklist_templates"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("template_code", ASCENDING)],
                unique=True,
                name="unique_offboarding_template",
            ),
        ]


class HrOffboardingProcess(Document):
    tenant_id: PydanticObjectId
    process_code: str = Field(max_length=64)
    resignation_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    template_id: PydanticObjectId
    status: HrOffboardingProcessStatus = HrOffboardingProcessStatus.IN_PROGRESS
    last_working_date: date | None = None
    separation_reason: str | None = Field(default=None, max_length=2000)
    payroll_handoff_sent: bool = False
    completed_at: datetime | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_offboarding_processes"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("process_code", ASCENDING)],
                unique=True,
                name="unique_offboarding_process",
            ),
        ]


class HrOffboardingTask(Document):
    tenant_id: PydanticObjectId
    process_id: PydanticObjectId
    task_key: str = Field(max_length=64)
    title: str = Field(max_length=200)
    clearance_department: str = Field(max_length=64)
    status: HrOffboardingTaskStatus = HrOffboardingTaskStatus.ASSIGNED
    remarks: str | None = Field(default=None, max_length=2000)
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_offboarding_tasks"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("process_id", ASCENDING), ("task_key", ASCENDING)],
                unique=True,
                name="unique_offboarding_task",
            ),
        ]


class HrExitInterview(Document):
    tenant_id: PydanticObjectId
    process_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    scheduled_at: datetime | None = None
    interviewer_id: PydanticObjectId | None = None
    reason_for_leaving: str | None = Field(default=None, max_length=2000)
    employee_feedback: str | None = Field(default=None, max_length=4000)
    department_feedback: str | None = Field(default=None, max_length=4000)
    improvement_suggestions: str | None = Field(default=None, max_length=4000)
    confidential_hr_remarks: str | None = Field(default=None, max_length=4000)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_exit_interviews"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("process_id", ASCENDING)], unique=True, name="unique_exit_interview"),
        ]