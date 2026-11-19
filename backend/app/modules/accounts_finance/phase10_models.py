"""Phase 10 procurement extensions and employee expense claims."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel

from app.common.time import utcnow
from app.modules.accounts_finance.phase10_enums import ExpenseClaimStatus, VendorVerificationStatus


class FinanceVendorBankDetail(Document):
    """Restricted bank details — not returned without finance:vendor:bank."""

    tenant_id: PydanticObjectId
    vendor_id: str
    bank_name: str | None = None
    account_holder: str | None = None
    account_number_ref: str
    ifsc: str | None = None
    updated_by: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_vendors"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("vendor_id", ASCENDING)], unique=True, name="unique_finance_vendor_bank"),
        ]


class FinanceVendorVerificationHistory(Document):
    tenant_id: PydanticObjectId
    history_id: str
    vendor_id: str
    from_status: str | None = None
    to_status: str
    actor_id: PydanticObjectId | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_vendor_verification_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("history_id", ASCENDING)], unique=True, name="unique_vendor_verify_hist"),
        ]


class PurchaseRequestApprovalHistory(Document):
    tenant_id: PydanticObjectId
    history_id: str
    request_id: str
    decision: str
    actor_id: PydanticObjectId
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "purchase_request_approval_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("history_id", ASCENDING)], unique=True, name="unique_pr_approval_hist"),
        ]


class PurchaseOrderItem(Document):
    tenant_id: PydanticObjectId
    item_id: str
    order_id: str
    description: str
    quantity: float = Field(ge=0)
    unit_price: float = Field(ge=0)
    line_total: float = Field(ge=0)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "purchase_order_items"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("item_id", ASCENDING)], unique=True, name="unique_po_item"),
        ]


class PurchaseOrderHistory(Document):
    tenant_id: PydanticObjectId
    history_id: str
    order_id: str
    action: str
    actor_id: PydanticObjectId | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "purchase_order_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("history_id", ASCENDING)], unique=True, name="unique_po_hist"),
        ]


class VendorInvoiceVerificationHistory(Document):
    tenant_id: PydanticObjectId
    history_id: str
    invoice_id: str
    status: str
    discrepancies: list[dict[str, Any]] = Field(default_factory=list)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "vendor_invoice_verification_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("history_id", ASCENDING)], unique=True, name="unique_vinv_verify_hist"),
        ]


class VendorPayable(Document):
    tenant_id: PydanticObjectId
    payable_id: str
    invoice_id: str
    vendor_id: str
    invoice_amount: float = Field(ge=0)
    adjustments: float = Field(default=0)
    amount_paid: float = Field(default=0, ge=0)
    outstanding: float = Field(ge=0)
    due_date: date | None = None
    payment_status: str = "pending"
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "vendor_payables"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("payable_id", ASCENDING)], unique=True, name="unique_vendor_payable"),
            IndexModel([("tenant_id", ASCENDING), ("invoice_id", ASCENDING)], unique=True, name="unique_payable_per_invoice"),
        ]


class VendorPayment(Document):
    tenant_id: PydanticObjectId
    payment_id: str
    vendor_id: str
    invoice_id: str
    amount: float = Field(gt=0)
    payment_reference: str
    status: str = "confirmed"
    initiated_by: PydanticObjectId
    approved_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "vendor_payments"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("payment_id", ASCENDING)], unique=True, name="unique_vendor_payment"),
        ]


class VendorCreditNote(Document):
    tenant_id: PydanticObjectId
    credit_note_id: str
    vendor_id: str
    invoice_id: str
    amount: float = Field(gt=0)
    reason: str
    status: str = "approved"
    created_by: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "vendor_credit_notes"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("credit_note_id", ASCENDING)], unique=True, name="unique_vendor_credit_note"),
        ]


class FinanceExpenseCategory(Document):
    tenant_id: PydanticObjectId
    category_code: str
    label: str
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_expense_categories"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("category_code", ASCENDING)], unique=True, name="unique_expense_category"),
        ]


class FinanceExpensePolicy(Document):
    tenant_id: PydanticObjectId
    policy_id: str
    category_code: str
    max_amount: float | None = None
    per_day_limit: float | None = None
    requires_pre_approval: bool = False
    requires_documents: bool = True
    eligible_roles: list[str] = Field(default_factory=list)
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_expense_policies"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("policy_id", ASCENDING)], unique=True, name="unique_expense_policy"),
        ]


class EmployeeExpenseClaim(Document):
    tenant_id: PydanticObjectId
    claim_id: str
    claim_number: str
    requester_id: PydanticObjectId
    department_id: PydanticObjectId | None = None
    category_code: str
    expense_date: date
    amount: float = Field(gt=0)
    currency: str = "INR"
    description: str
    business_purpose: str | None = None
    vendor_id: str | None = None
    document_refs: list[str] = Field(default_factory=list)
    finance_budget_id: str | None = None
    cost_centre_code: str | None = None
    bill_fingerprint: str | None = None
    status: ExpenseClaimStatus = ExpenseClaimStatus.DRAFT
    approved_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_expense_claims"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("claim_id", ASCENDING)], unique=True, name="unique_expense_claim"),
            IndexModel([("tenant_id", ASCENDING), ("bill_fingerprint", ASCENDING)], unique=True, sparse=True, name="unique_bill_fingerprint"),
        ]


class EmployeeExpenseClaimItem(Document):
    tenant_id: PydanticObjectId
    item_id: str
    claim_id: str
    description: str
    amount: float = Field(gt=0)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_expense_claim_items"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("item_id", ASCENDING)], unique=True, name="unique_claim_item"),
        ]


class ExpenseApprovalHistory(Document):
    tenant_id: PydanticObjectId
    history_id: str
    claim_id: str
    from_status: str | None
    to_status: str
    actor_id: PydanticObjectId
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "expense_approval_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("history_id", ASCENDING)], unique=True, name="unique_expense_approval_hist"),
        ]


class ExpensePaymentRecord(Document):
    tenant_id: PydanticObjectId
    payment_record_id: str
    claim_id: str
    amount: float = Field(gt=0)
    payment_reference: str
    status: str = "confirmed"
    created_by: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "expense_payment_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("payment_record_id", ASCENDING)], unique=True, name="unique_expense_payment"),
        ]


class EmployeeAdvanceRecord(Document):
    tenant_id: PydanticObjectId
    advance_id: str
    employee_id: PydanticObjectId
    amount: float = Field(gt=0)
    purpose: str
    status: str = "approved"
    payment_reference: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_advance_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("advance_id", ASCENDING)], unique=True, name="unique_employee_advance"),
        ]


class EmployeeAdvanceSettlement(Document):
    tenant_id: PydanticObjectId
    settlement_id: str
    advance_id: str
    claim_id: str
    advance_used: float = Field(ge=0)
    refund_due: float = Field(default=0, ge=0)
    additional_payable: float = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_advance_settlements"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("settlement_id", ASCENDING)], unique=True, name="unique_advance_settlement"),
        ]


class DepartmentExpenseRecord(Document):
    tenant_id: PydanticObjectId
    record_id: str
    department_id: PydanticObjectId
    category_code: str
    amount: float = Field(gt=0)
    expense_date: date
    finance_budget_id: str | None = None
    cost_centre_code: str | None = None
    description: str
    status: str = "approved"
    created_by: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_expense_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("record_id", ASCENDING)], unique=True, name="unique_dept_expense_record"),
        ]