"""Employment change, probation, and contract records."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.hr.enums import HrEmploymentChangeStatus, HrEmploymentChangeType, HrProbationReviewStatus


class HrEmploymentChangeRequest(Document):
    tenant_id: PydanticObjectId
    change_code: str = Field(max_length=64)
    employee_user_id: PydanticObjectId
    change_type: HrEmploymentChangeType
    current_details: dict[str, Any] = Field(default_factory=dict)
    proposed_details: dict[str, Any] = Field(default_factory=dict)
    effective_date: date
    reason: str = Field(max_length=2000)
    requested_by: PydanticObjectId
    document_refs: list[str] = Field(default_factory=list)
    approval_levels: list[dict[str, Any]] = Field(default_factory=list)
    status: HrEmploymentChangeStatus = HrEmploymentChangeStatus.DRAFT
    review_note: str | None = Field(default=None, max_length=2000)
    applied_at: datetime | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_employment_change_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("change_code", ASCENDING)],
                unique=True,
                name="unique_employment_change_code",
            ),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="hr_changes_by_status"),
            IndexModel([("tenant_id", ASCENDING), ("employee_user_id", ASCENDING)], name="hr_changes_by_employee"),
        ]


class HrProbationReview(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    probation_start_date: date
    probation_end_date: date
    manager_feedback: str = Field(default="", max_length=4000)
    hr_review: str = Field(default="", max_length=4000)
    recommendation: str = Field(default="pending", max_length=64)
    status: HrProbationReviewStatus = HrProbationReviewStatus.DRAFT
    approved_by: PydanticObjectId | None = None
    approved_at: datetime | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_probation_reviews"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("employee_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="hr_probation_by_employee",
            ),
        ]


class HrContractRecord(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    contract_code: str = Field(max_length=64)
    contract_type: str = Field(max_length=64)
    start_date: date
    end_date: date | None = None
    renewal_eligible: bool = True
    document_ref: str | None = None
    status: str = Field(default="active", max_length=32)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_contract_records"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("contract_code", ASCENDING)],
                unique=True,
                name="unique_contract_code",
            ),
        ]