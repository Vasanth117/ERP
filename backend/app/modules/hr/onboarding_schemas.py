"""HR onboarding API schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.hr.enums import HrOnboardingProcessStatus, HrOnboardingTaskStatus
from app.modules.hr.onboarding_models import HrOnboardingChecklistTemplate, HrOnboardingProcess, HrOnboardingTask


class OnboardingTemplateUpsert(BaseModel):
    template_code: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=200)
    employee_category: str = Field(min_length=1, max_length=64)
    tasks: list[dict[str, Any]] = Field(min_length=1)


class OnboardingTemplateRead(BaseModel):
    id: str
    template_code: str
    title: str
    employee_category: str
    version: int

    @classmethod
    def from_document(cls, doc: HrOnboardingChecklistTemplate) -> "OnboardingTemplateRead":
        return cls(
            id=str(doc.id),
            template_code=doc.template_code,
            title=doc.title,
            employee_category=doc.employee_category,
            version=doc.version,
        )


class OnboardingInitiate(BaseModel):
    offer_id: str
    template_id: str
    department_id: str
    designation: str
    reporting_manager_id: str | None = None
    joining_date: date | None = None
    mandatory_document_requirements: list[str] = Field(default_factory=list)
    create_employee: bool = True
    employee_code: str | None = None
    institution_role: str | None = None


class OnboardingTaskUpdate(BaseModel):
    status: HrOnboardingTaskStatus
    remarks: str | None = Field(default=None, max_length=2000)
    document_ref: str | None = None


class OnboardingWaiverCreate(BaseModel):
    requirement_key: str = Field(min_length=1, max_length=128)
    reason: str = Field(min_length=1, max_length=2000)


class OnboardingProcessRead(BaseModel):
    id: str
    process_code: str
    offer_id: str
    candidate_id: str
    employee_user_id: str | None
    status: HrOnboardingProcessStatus
    joining_date: date | None

    @classmethod
    def from_document(cls, doc: HrOnboardingProcess) -> "OnboardingProcessRead":
        return cls(
            id=str(doc.id),
            process_code=doc.process_code,
            offer_id=str(doc.offer_id),
            candidate_id=str(doc.candidate_id),
            employee_user_id=str(doc.employee_user_id) if doc.employee_user_id else None,
            status=doc.status,
            joining_date=doc.joining_date,
        )


class OnboardingTaskRead(BaseModel):
    id: str
    task_key: str
    title: str
    responsible_role: str
    status: HrOnboardingTaskStatus
    mandatory: bool
    due_date: date | None

    @classmethod
    def from_document(cls, doc: HrOnboardingTask) -> "OnboardingTaskRead":
        return cls(
            id=str(doc.id),
            task_key=doc.task_key,
            title=doc.title,
            responsible_role=doc.responsible_role,
            status=doc.status,
            mandatory=doc.mandatory,
            due_date=doc.due_date,
        )


class OnboardingProgressRead(BaseModel):
    process_id: str
    overall_percent: float
    completed_tasks: int
    pending_tasks: int
    overdue_tasks: int
    blocked_tasks: int
    employee_side_percent: float
    hr_side_percent: float
    department_side_percent: float


class OnboardingOverviewStats(BaseModel):
    awaiting_onboarding: int = 0
    currently_onboarding: int = 0
    pending_tasks: int = 0
    overdue_tasks: int = 0
    pending_documents: int = 0
    pending_verifications: int = 0
    pending_approvals: int = 0
    completed: int = 0