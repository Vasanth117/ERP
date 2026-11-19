"""Offboarding API schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.hr.enums import HrOffboardingProcessStatus, HrOffboardingTaskStatus, HrResignationStatus
from app.modules.hr.offboarding_models import HrOffboardingProcess, HrOffboardingTask, HrResignationRequest


class ResignationCreate(BaseModel):
    employee_user_id: str
    proposed_last_working_date: date
    reason: str = Field(min_length=1, max_length=2000)
    employee_remarks: str | None = None
    document_refs: list[str] = Field(default_factory=list)
    notice_days: int = Field(ge=0, default=30)


class ResignationReview(BaseModel):
    decision: str = Field(pattern="^(manager_approve|hr_approve|accept|reject|withdraw)$")
    note: str | None = Field(default=None, max_length=2000)


class ResignationRead(BaseModel):
    id: str
    resignation_code: str
    employee_user_id: str
    status: HrResignationStatus
    proposed_last_working_date: date

    @classmethod
    def from_document(cls, doc: HrResignationRequest) -> "ResignationRead":
        return cls(
            id=str(doc.id),
            resignation_code=doc.resignation_code,
            employee_user_id=str(doc.employee_user_id),
            status=doc.status,
            proposed_last_working_date=doc.proposed_last_working_date,
        )


class OffboardingTemplateUpsert(BaseModel):
    template_code: str
    title: str
    tasks: list[dict[str, Any]]


class OffboardingInitiate(BaseModel):
    resignation_id: str
    template_id: str


class OffboardingTaskUpdate(BaseModel):
    status: HrOffboardingTaskStatus
    remarks: str | None = None


class ExitInterviewUpsert(BaseModel):
    scheduled_at: datetime | None = None
    interviewer_id: str | None = None
    reason_for_leaving: str | None = None
    employee_feedback: str | None = None
    department_feedback: str | None = None
    improvement_suggestions: str | None = None
    confidential_hr_remarks: str | None = None


class NoticePeriodUpdate(BaseModel):
    actual_last_working_date: date | None = None
    waiver_reason: str | None = None
    early_release: bool = False
    extension_days: int = Field(ge=0, default=0)
    note: str | None = Field(default=None, max_length=2000)


class OffboardingProcessRead(BaseModel):
    id: str
    process_code: str
    status: HrOffboardingProcessStatus

    @classmethod
    def from_document(cls, doc: HrOffboardingProcess) -> "OffboardingProcessRead":
        return cls(id=str(doc.id), process_code=doc.process_code, status=doc.status)