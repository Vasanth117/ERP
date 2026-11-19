"""Parent portal phase 3 API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.modules.students.examination_registration_schemas import HallTicketAvailabilityRead, HallTicketDownloadRead
from app.modules.students.examination_results_schemas import SemesterResultSummaryRead, SubjectWiseMarksRead
from app.modules.students.student_finance_schemas import (
    FeeDemandRead,
    FeeStructureRead,
    InstallmentScheduleRead,
    OutstandingDuesRead,
    PaymentHistoryRead,
    PaymentInitiateInput,
    PaymentInitiateRead,
    PaymentStatusRead,
    ReceiptRead,
    ScholarshipEligibilityRead,
)


class ParentExaminationOverviewRead(BaseModel):
    academic_year_label: str
    semester_label: str
    upcoming_count: int
    next_examination_at: datetime | None = None
    registration_open: bool | None = None
    primary_season_id: str | None = None


class ParentExamSessionRead(BaseModel):
    session_code: str
    season_id: str
    course_code: str
    section: str | None = None
    title: str
    scheduled_start: datetime
    scheduled_end: datetime | None = None
    venue: str | None = None
    instructions: str | None = None


class ParentExamTimetableRead(BaseModel):
    academic_year_label: str
    semester_label: str
    sessions: list[ParentExamSessionRead] = Field(default_factory=list)


class ParentExamCalendarEventRead(BaseModel):
    id: str
    title: str
    event_at: datetime
    event_type: str
    description: str | None = None


class ParentExamNotificationRead(BaseModel):
    notification_id: str
    category: str
    title: str
    body: str
    read: bool
    created_at: datetime


class ParentExamResultStatusRead(BaseModel):
    season_id: str
    status: str
    published: bool
    published_at: datetime | None = None


class ParentExamReviewStatusRead(BaseModel):
    request_id: str
    request_type: str
    course_code: str
    season_id: str
    status: str
    revised_mark_published: bool = False


class ParentFinanceDashboardRead(BaseModel):
    outstanding: OutstandingDuesRead
    fee_structures: list[FeeStructureRead] = Field(default_factory=list)
    recent_payments: list[PaymentHistoryRead] = Field(default_factory=list)
    receipt_count: int = 0
    scholarships_eligible: int = 0


class ParentFinanceStatementLineRead(BaseModel):
    demand_id: str
    description: str
    original_amount: float
    net_payable: float
    amount_paid: float = 0
    outstanding: float
    due_date: date
    status: str


class ParentFinanceStatementRead(BaseModel):
    lines: list[ParentFinanceStatementLineRead] = Field(default_factory=list)
    total_outstanding: float


class ParentFinanceEnquiryCreate(BaseModel):
    category: str
    transaction_id: str | None = None
    receipt_id: str | None = None
    description: str = Field(min_length=10, max_length=4000)


class ParentFinanceEnquiryRead(BaseModel):
    enquiry_id: str
    category: str
    status: str
    description: str
    response_notes: str | None = None
    created_at: datetime


class ParentPaymentInitiateInput(PaymentInitiateInput):
    """Same validation as student payments; initiated by parent on behalf of student."""