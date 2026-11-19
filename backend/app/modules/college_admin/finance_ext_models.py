"""Institutional finance extensions (budgets, procurement — not student fee core)."""

from datetime import date, datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class BudgetStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"


class ExpenseStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class PurchaseRequestStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    ORDERED = "ordered"


class PurchaseOrderStatus(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    PARTIAL = "partial"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"


class InvoicePaymentStatus(str, Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    CANCELLED = "cancelled"


class InstitutionBudget(Document):
    tenant_id: PydanticObjectId
    budget_id: str
    label: str
    fiscal_year: str
    period_start: date
    period_end: date
    total_amount: float = Field(ge=0)
    currency: str = "INR"
    status: BudgetStatus = BudgetStatus.DRAFT
    enabled: bool = True
    updated_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_budgets"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("budget_id", ASCENDING)], unique=True, name="unique_institution_budget"),
        ]


class DepartmentBudgetAllocation(Document):
    tenant_id: PydanticObjectId
    allocation_id: str
    budget_id: str
    department_id: PydanticObjectId
    allocated_amount: float = Field(ge=0)
    utilized_amount: float = Field(default=0, ge=0)
    actor_id: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_budget_allocations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("budget_id", ASCENDING), ("department_id", ASCENDING)],
                unique=True,
                name="unique_dept_budget_alloc",
            ),
        ]


class InstitutionBudgetTransaction(Document):
    tenant_id: PydanticObjectId
    transaction_id: str
    budget_id: str
    department_id: PydanticObjectId | None = None
    amount: float = Field(ge=0)
    direction: str = "debit"
    reference_type: str
    reference_id: str
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_budget_transactions"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("budget_id", ASCENDING), ("created_at", DESCENDING)], name="budget_tx_by_budget"),
        ]


class InstitutionExpenseRecord(Document):
    tenant_id: PydanticObjectId
    expense_id: str
    budget_id: str | None = None
    department_id: PydanticObjectId | None = None
    title: str = Field(max_length=200)
    amount: float = Field(ge=0)
    status: ExpenseStatus = ExpenseStatus.DRAFT
    workflow_instance_id: str | None = None
    asset_id: str | None = None
    actor_id: PydanticObjectId | None = None
    approved_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_expense_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("expense_id", ASCENDING)], unique=True, name="unique_expense"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="expenses_by_status"),
        ]


class InstitutionVendorRecord(Document):
    tenant_id: PydanticObjectId
    vendor_id: str
    name: str
    vendor_code: str | None = None
    category: str | None = None
    gstin: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    address: str | None = None
    authorized_representative: str | None = None
    verification_status: str = "pending"
    vendor_status: str = "active"
    document_refs: list[str] = Field(default_factory=list)
    active: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_vendor_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("vendor_id", ASCENDING)], unique=True, name="unique_vendor"),
            IndexModel(
                [("tenant_id", ASCENDING), ("vendor_code", ASCENDING)],
                unique=True,
                sparse=True,
                name="unique_vendor_code",
            ),
        ]


class InstitutionPurchaseRequest(Document):
    tenant_id: PydanticObjectId
    request_id: str
    request_number: str | None = None
    vendor_id: str | None = None
    department_id: PydanticObjectId | None = None
    budget_id: str | None = None
    finance_budget_id: str | None = None
    cost_centre_code: str | None = None
    description: str = Field(max_length=2000)
    quantity: float = Field(default=1, ge=0)
    estimated_unit_cost: float | None = None
    estimated_amount: float = Field(ge=0)
    required_date: date | None = None
    priority: str = "normal"
    reason: str | None = None
    document_refs: list[str] = Field(default_factory=list)
    requested_by: PydanticObjectId | None = None
    status: PurchaseRequestStatus = PurchaseRequestStatus.DRAFT
    workflow_instance_id: str | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_purchase_requests"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("request_id", ASCENDING)], unique=True, name="unique_purchase_request"),
        ]


class InstitutionPurchaseOrder(Document):
    tenant_id: PydanticObjectId
    order_id: str
    request_id: str | None = None
    vendor_id: str
    finance_budget_id: str | None = None
    cost_centre_code: str | None = None
    total_amount: float = Field(ge=0)
    tax_amount: float = Field(default=0, ge=0)
    payment_terms: str | None = None
    delivery_terms: str | None = None
    expected_delivery: date | None = None
    published: bool = False
    status: PurchaseOrderStatus = PurchaseOrderStatus.DRAFT
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_purchase_orders"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("order_id", ASCENDING)], unique=True, name="unique_purchase_order"),
        ]


class InstitutionVendorInvoice(Document):
    tenant_id: PydanticObjectId
    invoice_id: str
    vendor_invoice_number: str | None = None
    vendor_id: str
    order_id: str | None = None
    invoice_date: date | None = None
    amount: float = Field(ge=0)
    tax_amount: float = Field(default=0, ge=0)
    discount_amount: float = Field(default=0, ge=0)
    total_payable: float | None = None
    paid_amount: float = Field(default=0, ge=0)
    verification_status: str = "pending"
    payment_status: InvoicePaymentStatus = InvoicePaymentStatus.PENDING
    due_date: date | None = None
    document_refs: list[str] = Field(default_factory=list)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_vendor_invoices"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("invoice_id", ASCENDING)], unique=True, name="unique_vendor_invoice"),
        ]