"""Mess management API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.modules.hostel.mess_models import (
    MessBillingMethod,
    MessBillingRecordStatus,
    MessEnrollmentStatus,
    MessFacilityStatus,
    MessPlanStatus,
)


class HostelMessCreate(BaseModel):
    mess_code: str = Field(max_length=32)
    name: str = Field(max_length=200)
    hostel_codes: list[str] = Field(default_factory=list)
    building_codes: list[str] = Field(default_factory=list)
    capacity: int | None = Field(default=None, ge=0)
    operating_hours: dict = Field(default_factory=dict)
    supervisor_user_ids: list[str] = Field(default_factory=list)
    status: MessFacilityStatus = MessFacilityStatus.ACTIVE


class HostelMessRead(BaseModel):
    mess_code: str
    name: str
    hostel_codes: list[str]
    building_codes: list[str]
    capacity: int | None
    operating_hours: dict
    supervisor_user_ids: list[str]
    status: MessFacilityStatus
    updated_at: datetime


class MessPlanUpsertPortal(BaseModel):
    plan_code: str = Field(max_length=32)
    title: str = Field(max_length=200)
    description: str | None = None
    mess_code: str | None = None
    included_meals: list[str] = Field(default_factory=list)
    billing_method: MessBillingMethod = MessBillingMethod.FIXED_MONTHLY
    monthly_amount: float = Field(ge=0)
    billing_frequency: str = "monthly"
    effective_from: date | None = None
    effective_to: date | None = None
    requires_approval: bool = True
    published: bool = False
    status: MessPlanStatus = MessPlanStatus.ACTIVE
    finance_reference: str | None = None


class MessPlanRead(BaseModel):
    plan_code: str
    title: str
    mess_code: str | None
    monthly_amount: float
    billing_method: MessBillingMethod
    published: bool
    status: MessPlanStatus
    included_meals: list[str]
    finance_reference: str | None
    updated_at: datetime


class MealCategoryUpsert(BaseModel):
    category_code: str
    label: str
    mess_code: str | None = None
    default_start_time: str | None = None
    default_end_time: str | None = None
    serving_days: list[str] = Field(default_factory=list)
    active: bool = True


class MenuUpsert(BaseModel):
    menu_id: str | None = None
    mess_code: str
    menu_scope: str = "daily"
    meal_category_code: str | None = None
    service_date: date | None = None
    items: list[dict] = Field(default_factory=list)
    dietary_labels: list[str] = Field(default_factory=list)
    publish: bool = False


class MenuRead(BaseModel):
    menu_id: str
    mess_code: str
    menu_scope: str
    service_date: date | None
    items: list[dict]
    published: bool
    revision: int
    updated_at: datetime


class MessEnrollmentCreate(BaseModel):
    resident_id: str
    plan_code: str
    mess_code: str
    start_date: date
    end_date: date | None = None


class MessEnrollmentRead(BaseModel):
    enrollment_id: str
    resident_id: str
    student_user_id: str
    mess_code: str
    plan_code: str
    start_date: date
    end_date: date | None
    status: MessEnrollmentStatus
    rate_snapshot: float


class MessEnrollmentDecision(BaseModel):
    enrollment_id: str
    approve: bool
    note: str | None = None


class MealAttendanceRecord(BaseModel):
    enrollment_id: str
    meal_category_code: str
    service_date: date
    attended: bool = True
    exemption_reason: str | None = None
    capture_method: str = "staff_entry"


class BillingPeriodCreate(BaseModel):
    period_id: str | None = None
    label: str
    mess_code: str | None = None
    period_start: date
    period_end: date


class BillingPeriodRead(BaseModel):
    period_id: str
    label: str
    mess_code: str | None
    period_start: date
    period_end: date
    status: str


class BillingCalculateInput(BaseModel):
    period_id: str


class BillingRecordRead(BaseModel):
    record_id: str
    period_id: str
    enrollment_id: str
    student_user_id: str
    amount: float
    status: MessBillingRecordStatus
    finance_demand_id: str | None


class BillingRecordApprove(BaseModel):
    record_id: str


class BillingSendFinanceInput(BaseModel):
    period_id: str


class BillingAdjustmentCreate(BaseModel):
    enrollment_id: str
    amount_delta: float
    reason: str
    source_type: str = "leave_exemption"
    source_ref: str | None = None


class MessEnrollmentReport(BaseModel):
    active_enrollments: int
    plan_breakdown: dict[str, int]