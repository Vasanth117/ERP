"""Student finance API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class FeeStructureRead(BaseModel):
    structure_id: str
    academic_year_label: str
    semester_label: str
    line_items: list[dict] = Field(default_factory=list)
    total_amount: float


class FeeDemandRead(BaseModel):
    demand_id: str
    description: str
    amount: float
    due_date: date
    status: str
    late_fee: float = 0


class OutstandingDuesRead(BaseModel):
    total_outstanding: float
    demands: list[FeeDemandRead] = Field(default_factory=list)


class PaymentInitiateInput(BaseModel):
    demand_id: str
    idempotency_key: str = Field(min_length=8, max_length=64)
    payment_mode: str = Field(default="online", pattern=r"^(online|offline)$")
    offline_reference: str | None = Field(default=None, max_length=120)

    model_config = {"extra": "forbid"}


class PaymentInitiateRead(BaseModel):
    transaction_id: str
    status: str
    amount: float
    gateway: str


class PaymentStatusRead(BaseModel):
    transaction_id: str
    status: str
    webhook_verified: bool
    gateway_reference: str | None = None


class PaymentHistoryRead(BaseModel):
    transaction_id: str
    amount: float
    status: str
    created_at: datetime


class ReceiptRead(BaseModel):
    receipt_id: str
    transaction_id: str
    amount: float
    issued_at: datetime
    download_token: str | None = None


class InstallmentScheduleRead(BaseModel):
    schedule_id: str
    installments: list[dict] = Field(default_factory=list)


class ScholarshipEligibilityRead(BaseModel):
    programme_id: str
    eligible: bool
    reasons: list[str] = Field(default_factory=list)


class ScholarshipApplicationInput(BaseModel):
    programme_id: str
    statement: str | None = Field(default=None, max_length=4000)

    model_config = {"extra": "forbid"}


class ScholarshipApplicationRead(BaseModel):
    application_id: str
    programme_id: str
    status: str
    created_at: datetime


class ConcessionRead(BaseModel):
    concession_id: str
    title: str
    amount: float
    percent: float | None = None


class RefundStatusRead(BaseModel):
    refund_id: str
    amount: float
    status: str
    transaction_id: str | None = None


class LedgerEntryRead(BaseModel):
    entry_id: str
    entry_type: str
    description: str
    debit: float
    credit: float
    balance_after: float
    posted_at: datetime
