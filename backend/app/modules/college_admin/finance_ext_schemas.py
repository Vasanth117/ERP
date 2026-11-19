"""Finance extension API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.modules.college_admin.finance_ext_models import (
    BudgetStatus,
    ExpenseStatus,
    InvoicePaymentStatus,
    PurchaseOrderStatus,
    PurchaseRequestStatus,
)


class BudgetUpsert(BaseModel):
    budget_id: str
    label: str
    fiscal_year: str
    period_start: date
    period_end: date
    total_amount: float = Field(ge=0)
    status: BudgetStatus = BudgetStatus.ACTIVE


class BudgetRead(BaseModel):
    budget_id: str
    label: str
    fiscal_year: str
    total_amount: float
    status: BudgetStatus
    utilized: float
    variance: float


class BudgetAllocationUpsert(BaseModel):
    allocation_id: str
    budget_id: str
    department_id: str
    allocated_amount: float = Field(ge=0)


class ExpenseCreate(BaseModel):
    expense_id: str
    title: str
    amount: float = Field(ge=0)
    budget_id: str | None = None
    department_id: str | None = None
    asset_id: str | None = None
    submit_for_approval: bool = False


class ExpenseApprove(BaseModel):
    approved: bool = True
    note: str | None = None


class VendorUpsert(BaseModel):
    vendor_id: str
    name: str
    gstin: str | None = None
    contact_email: str | None = None


class PurchaseRequestCreate(BaseModel):
    request_id: str
    description: str
    estimated_amount: float = Field(ge=0)
    vendor_id: str | None = None
    department_id: str | None = None
    budget_id: str | None = None
    submit: bool = False


class PurchaseRequestApprove(BaseModel):
    approved: bool = True


class PurchaseOrderCreate(BaseModel):
    order_id: str
    request_id: str | None = None
    vendor_id: str
    total_amount: float = Field(ge=0)


class VendorInvoiceCreate(BaseModel):
    invoice_id: str
    vendor_id: str
    amount: float = Field(ge=0)
    order_id: str | None = None
    due_date: date | None = None


class BudgetReportRead(BaseModel):
    budget_id: str
    total: float
    allocated: float
    utilized: float
    variance: float
    expense_count: int