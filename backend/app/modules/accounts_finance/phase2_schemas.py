"""Phase 2 assessment and invoice API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.modules.accounts_finance.phase2_enums import FeeAssessmentWorkflowStatus, StudentInvoiceStatus


class AssessmentScopeFilter(BaseModel):
    academic_year_label: str
    semester_label: str
    programme_code: str | None = None
    department_id: str | None = None
    batch_label: str | None = None
    campus_id: str | None = None
    student_category: str | None = None
    admission_type: str | None = None


class AssessmentPreviewResult(BaseModel):
    batch_id: str
    eligible_count: int
    exception_count: int
    exceptions: list[dict]


class IndividualAssessmentCreate(BaseModel):
    student_user_id: str
    academic_year_label: str
    semester_label: str
    structure_id: str | None = None
    optional_fee_category_codes: list[str] = Field(default_factory=list)
    waiver_amount: float = Field(default=0, ge=0)


class BulkAssessmentCreate(AssessmentScopeFilter):
    batch_id: str | None = None
    structure_id: str | None = None
    optional_fee_category_codes: list[str] = Field(default_factory=list)


class AssessmentTransition(BaseModel):
    action: str = Field(description="submit|approve|return|cancel")
    note: str | None = None


class AssessmentItemRead(BaseModel):
    item_id: str
    fee_category_code: str
    description: str
    original_amount: float
    adjustment_amount: float
    net_amount: float
    mandatory: bool
    optional_selected: bool


class AssessmentRead(BaseModel):
    assessment_id: str
    student_user_id: str
    structure_id: str
    academic_year_label: str
    semester_label: str
    workflow_status: FeeAssessmentWorkflowStatus | str
    assessed_amount: float
    mandatory_amount: float
    optional_amount: float
    scholarship_amount: float
    concession_amount: float
    waiver_amount: float
    adjustment_amount: float
    net_amount: float
    invoice_id: str | None = None
    items: list[AssessmentItemRead]
    created_at: datetime
    updated_at: datetime


class InvoiceGenerateScope(BaseModel):
    academic_year_label: str
    semester_label: str
    programme_code: str | None = None
    department_id: str | None = None
    assessment_ids: list[str] = Field(default_factory=list)
    due_date: date
    billing_date: date | None = None


class InvoiceGeneratePreview(BaseModel):
    eligible_assessments: int
    would_create: int
    duplicate_blocked: int


class InvoiceIssueRequest(BaseModel):
    note: str | None = None


class InvoiceAdjustmentRequest(BaseModel):
    adjustment_type: str = Field(description="credit_note|debit_note|cancellation")
    amount: float = Field(ge=0)
    reason: str = Field(min_length=3, max_length=500)


class InvoiceItemRead(BaseModel):
    item_id: str
    fee_category_code: str
    description: str
    original_amount: float
    adjustment_amount: float
    net_amount: float


class InvoiceRead(BaseModel):
    invoice_id: str
    invoice_number: str | None
    student_user_id: str
    assessment_id: str | None
    academic_year_label: str | None
    semester_label: str | None
    original_amount: float
    amount: float
    invoice_status: StudentInvoiceStatus | str
    billing_date: date | None
    due_date: date
    issued_at: datetime
    published: bool
    items: list[InvoiceItemRead]
    payment_status_synced: str | None = None


class InvoiceSearchFilters(BaseModel):
    student_user_id: str | None = None
    roll_number: str | None = None
    invoice_number: str | None = None
    academic_year_label: str | None = None
    semester_label: str | None = None
    programme_code: str | None = None
    invoice_status: str | None = None
    due_before: date | None = None