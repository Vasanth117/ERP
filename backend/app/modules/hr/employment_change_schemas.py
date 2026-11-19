"""Employment change API schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.hr.enums import HrEmploymentChangeStatus, HrEmploymentChangeType, HrProbationReviewStatus
from app.modules.hr.employment_change_models import HrContractRecord, HrEmploymentChangeRequest, HrProbationReview


class EmploymentChangeOverview(BaseModel):
    pending: int = 0
    approved: int = 0
    awaiting_effective_date: int = 0
    department_transfers: int = 0
    designation_changes: int = 0
    reporting_manager_changes: int = 0
    employment_type_changes: int = 0
    probation_items: int = 0
    probation_approaching_end: int = 0
    contract_extensions: int = 0
    contracts_expiring_soon: int = 0
    salary_related_requests: int = 0
    resignations_active: int = 0
    notice_period: int = 0
    exit_in_progress: int = 0
    completed_exits: int = 0


class ProbationApproachingItem(BaseModel):
    employee_user_id: str
    probation_end_date: date
    days_remaining: int


class ContractRecordRead(BaseModel):
    id: str
    employee_user_id: str
    contract_code: str
    contract_type: str
    start_date: date
    end_date: date | None
    renewal_eligible: bool
    status: str

    @classmethod
    def from_document(cls, doc: HrContractRecord) -> "ContractRecordRead":
        return cls(
            id=str(doc.id),
            employee_user_id=str(doc.employee_user_id),
            contract_code=doc.contract_code,
            contract_type=doc.contract_type,
            start_date=doc.start_date,
            end_date=doc.end_date,
            renewal_eligible=doc.renewal_eligible,
            status=doc.status,
        )


class EmploymentChangeCreate(BaseModel):
    employee_user_id: str
    change_type: HrEmploymentChangeType
    proposed_details: dict[str, Any]
    effective_date: date
    reason: str = Field(min_length=1, max_length=2000)
    document_refs: list[str] = Field(default_factory=list)
    requires_manager_approval: bool = True


class EmploymentChangeReview(BaseModel):
    decision: str = Field(pattern="^(approve|reject|return|hr_validate|manager_approve)$")
    note: str | None = Field(default=None, max_length=2000)


class EmploymentChangeRead(BaseModel):
    id: str
    change_code: str
    employee_user_id: str
    change_type: HrEmploymentChangeType
    status: HrEmploymentChangeStatus
    effective_date: date

    @classmethod
    def from_document(cls, doc: HrEmploymentChangeRequest) -> "EmploymentChangeRead":
        return cls(
            id=str(doc.id),
            change_code=doc.change_code,
            employee_user_id=str(doc.employee_user_id),
            change_type=doc.change_type,
            status=doc.status,
            effective_date=doc.effective_date,
        )


class EmploymentChangeDetailRead(EmploymentChangeRead):
    current_details: dict[str, Any]
    proposed_details: dict[str, Any]
    reason: str
    document_refs: list[str]
    review_note: str | None = None

    @classmethod
    def from_document(cls, doc: HrEmploymentChangeRequest) -> "EmploymentChangeDetailRead":
        base = EmploymentChangeRead.from_document(doc)
        return cls(
            **base.model_dump(),
            current_details=doc.current_details,
            proposed_details=doc.proposed_details,
            reason=doc.reason,
            document_refs=doc.document_refs,
            review_note=doc.review_note,
        )


class ProbationReviewUpsert(BaseModel):
    employee_user_id: str
    manager_feedback: str = ""
    hr_review: str = ""
    recommendation: str = Field(pattern="^(confirm|extend|reject|pending)$")


class ProbationReviewRead(BaseModel):
    id: str
    employee_user_id: str
    status: HrProbationReviewStatus
    probation_end_date: date

    @classmethod
    def from_document(cls, doc: HrProbationReview) -> "ProbationReviewRead":
        return cls(
            id=str(doc.id),
            employee_user_id=str(doc.employee_user_id),
            status=doc.status,
            probation_end_date=doc.probation_end_date,
        )


class ContractUpsert(BaseModel):
    employee_user_id: str
    contract_code: str
    contract_type: str
    start_date: date
    end_date: date | None = None
    renewal_eligible: bool = True
    document_ref: str | None = None