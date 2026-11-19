"""Accounts / Finance Staff collections (fee catalog & structures)."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.accounts_finance.enums import (
    BillingFrequency,
    FeeCategoryClassification,
    FeeStructureLifecycleStatus,
    RefundabilityClass,
)


class FinanceFeeCategory(Document):
    tenant_id: PydanticObjectId
    fee_code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    classification: FeeCategoryClassification = FeeCategoryClassification.OTHER
    programme_codes: list[str] = Field(default_factory=list)
    student_categories: list[str] = Field(default_factory=list)
    mandatory: bool = True
    optional_flag: bool = False
    refundability: RefundabilityClass = Field(default=RefundabilityClass.NON_REFUNDABLE)
    tax_reference: str | None = Field(default=None, max_length=64)
    active: bool = True
    created_by: PydanticObjectId | None = None
    updated_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "fee_categories"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("fee_code", ASCENDING)],
                unique=True,
                name="unique_fee_category_code",
            ),
            IndexModel([("tenant_id", ASCENDING), ("active", ASCENDING)], name="fee_categories_active"),
        ]


class FinanceFeeStructure(Document):
    tenant_id: PydanticObjectId
    structure_id: str = Field(min_length=2, max_length=64)
    template_key: str | None = Field(default=None, max_length=64)
    academic_year_label: str
    semester_label: str
    programme_code: str
    department_id: PydanticObjectId | None = None
    batch_year: str | None = None
    student_category: str | None = None
    campus_id: PydanticObjectId | None = None
    admission_type: str | None = None
    status: FeeStructureLifecycleStatus = FeeStructureLifecycleStatus.DRAFT
    version: int = 1
    effective_from: date | None = None
    effective_to: date | None = None
    total_amount: float = Field(default=0, ge=0)
    installment_eligible: bool = False
    authoritative_student_structure_id: PydanticObjectId | None = None
    superseded_by: str | None = None
    created_by: PydanticObjectId | None = None
    approved_by: PydanticObjectId | None = None
    approved_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "fee_structures"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("structure_id", ASCENDING)],
                unique=True,
                name="unique_finance_fee_structure",
            ),
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("programme_code", ASCENDING),
                    ("academic_year_label", ASCENDING),
                    ("semester_label", ASCENDING),
                    ("status", ASCENDING),
                ],
                name="fee_structures_scope",
            ),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="fee_structures_by_status"),
        ]


class FinanceFeeStructureComponent(Document):
    tenant_id: PydanticObjectId
    component_id: str = Field(min_length=2, max_length=64)
    structure_id: str
    fee_category_code: str
    amount: float = Field(ge=0)
    due_date: date | None = None
    billing_frequency: BillingFrequency = BillingFrequency.ONE_TIME
    student_group: str | None = None
    mandatory: bool = True
    optional_flag: bool = False
    refundability: RefundabilityClass = Field(default=RefundabilityClass.NON_REFUNDABLE)
    installment_eligible: bool = False
    effective_from: date | None = None
    effective_to: date | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "fee_structure_components"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("structure_id", ASCENDING), ("component_id", ASCENDING)],
                unique=True,
                name="unique_fee_structure_component",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("structure_id", ASCENDING)],
                name="fee_components_by_structure",
            ),
        ]


class FinanceFeeStructureVersion(Document):
    tenant_id: PydanticObjectId
    structure_id: str
    version: int
    reason: str | None = None
    effective_date: date | None = None
    requested_by: PydanticObjectId | None = None
    previous_snapshot: dict[str, Any] = Field(default_factory=dict)
    new_snapshot: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "fee_structure_versions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("structure_id", ASCENDING), ("version", ASCENDING)],
                unique=True,
                name="unique_fee_structure_version",
            ),
        ]


class FinanceFeeStructureApprovalHistory(Document):
    tenant_id: PydanticObjectId
    structure_id: str
    action: str
    from_status: str | None = None
    to_status: str | None = None
    actor_id: PydanticObjectId
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "fee_structure_approval_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("structure_id", ASCENDING), ("created_at", DESCENDING)],
                name="fee_structure_approval_trail",
            ),
        ]