"""Hostel mess management and billing collections."""

from datetime import date, datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class MessFacilityStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class MessPlanStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"


class MessBillingMethod(str, Enum):
    FIXED_MONTHLY = "fixed_monthly"
    PER_MEAL = "per_meal"
    SELECTED_MEALS = "selected_meals"
    DAILY = "daily"
    CUSTOM = "custom"


class MessEnrollmentStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    ENDED = "ended"


class MessBillingPeriodStatus(str, Enum):
    NOT_STARTED = "not_started"
    DRAFT = "draft"
    CALCULATING = "calculating"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SENT_TO_FINANCE = "sent_to_finance"
    RECONCILED = "reconciled"
    CANCELLED = "cancelled"


class MessBillingRecordStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SENT_TO_FINANCE = "sent_to_finance"
    INVOICE_GENERATED = "invoice_generated"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    PAYMENT_FAILED = "payment_failed"
    CANCELLED = "cancelled"
    RECONCILED = "reconciled"


class HostelMess(Document):
    tenant_id: PydanticObjectId
    mess_code: str
    name: str
    hostel_codes: list[str] = Field(default_factory=list)
    building_codes: list[str] = Field(default_factory=list)
    capacity: int | None = Field(default=None, ge=0)
    operating_hours: dict[str, Any] = Field(default_factory=dict)
    supervisor_user_ids: list[str] = Field(default_factory=list)
    status: MessFacilityStatus = MessFacilityStatus.ACTIVE
    history_note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_messes"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("mess_code", ASCENDING)], unique=True, name="unique_hostel_mess"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="mess_by_status"),
        ]


class HostelMessPlan(Document):
    """Mess meal plan (extends legacy college-admin fields)."""

    tenant_id: PydanticObjectId
    plan_code: str
    title: str
    description: str | None = None
    mess_code: str | None = None
    included_meals: list[str] = Field(default_factory=list)
    resident_categories: list[str] = Field(default_factory=list)
    billing_method: MessBillingMethod = MessBillingMethod.FIXED_MONTHLY
    monthly_amount: float = Field(default=0, ge=0)
    rate: float | None = Field(default=None, ge=0)
    billing_frequency: str = "monthly"
    effective_from: date | None = None
    effective_to: date | None = None
    enrollment_rules: dict[str, Any] = Field(default_factory=dict)
    cancellation_rules: dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = True
    finance_reference: str | None = None
    published: bool = False
    status: MessPlanStatus = MessPlanStatus.DRAFT
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_mess_plans"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("plan_code", ASCENDING)], unique=True, name="unique_mess_plan"),
            IndexModel([("tenant_id", ASCENDING), ("mess_code", ASCENDING), ("status", ASCENDING)], name="plans_by_mess"),
        ]


class HostelMealCategory(Document):
    tenant_id: PydanticObjectId
    category_code: str
    label: str
    mess_code: str | None = None
    default_start_time: str | None = None
    default_end_time: str | None = None
    serving_days: list[str] = Field(default_factory=list)
    active: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_meal_categories"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("category_code", ASCENDING)], unique=True, name="unique_meal_category"),
        ]


class HostelMealSchedule(Document):
    tenant_id: PydanticObjectId
    schedule_id: str
    mess_code: str
    schedule_type: str = "weekly"
    entries: list[dict[str, Any]] = Field(default_factory=list)
    holiday_dates: list[date] = Field(default_factory=list)
    effective_from: date | None = None
    effective_to: date | None = None
    published: bool = False
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_meal_schedules"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("schedule_id", ASCENDING)], unique=True, name="unique_meal_schedule"),
            IndexModel([("tenant_id", ASCENDING), ("mess_code", ASCENDING)], name="schedules_by_mess"),
        ]


class HostelMenu(Document):
    tenant_id: PydanticObjectId
    menu_id: str
    mess_code: str
    menu_scope: str = "daily"
    meal_category_code: str | None = None
    service_date: date | None = None
    week_label: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)
    dietary_labels: list[str] = Field(default_factory=list)
    revision: int = 1
    published: bool = False
    published_at: datetime | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_menus"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("menu_id", ASCENDING)], unique=True, name="unique_hostel_menu"),
            IndexModel([("tenant_id", ASCENDING), ("mess_code", ASCENDING), ("service_date", DESCENDING)], name="menus_by_date"),
        ]


class HostelMessEnrollment(Document):
    tenant_id: PydanticObjectId
    enrollment_id: str
    resident_id: str
    student_user_id: PydanticObjectId
    mess_code: str
    plan_code: str
    start_date: date
    end_date: date | None = None
    status: MessEnrollmentStatus = MessEnrollmentStatus.PENDING_APPROVAL
    rate_snapshot: float = Field(ge=0)
    billing_method: MessBillingMethod = MessBillingMethod.FIXED_MONTHLY
    approved_by: PydanticObjectId | None = None
    approved_at: datetime | None = None
    pause_reason: str | None = None
    cancelled_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_mess_enrollments"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("enrollment_id", ASCENDING)], unique=True, name="unique_mess_enrollment"),
            IndexModel(
                [("tenant_id", ASCENDING), ("resident_id", ASCENDING)],
                unique=True,
                name="unique_active_resident_mess",
                partialFilterExpression={"status": {"$in": ["pending_approval", "active", "paused"]}},
            ),
            IndexModel([("tenant_id", ASCENDING), ("plan_code", ASCENDING), ("status", ASCENDING)], name="enrollments_by_plan"),
        ]


class HostelMealAttendance(Document):
    tenant_id: PydanticObjectId
    attendance_id: str
    enrollment_id: str
    student_user_id: PydanticObjectId
    mess_code: str
    meal_category_code: str
    service_date: date
    attended: bool = True
    capture_method: str = "staff_entry"
    exemption_reason: str | None = None
    recorded_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_meal_attendance"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("attendance_id", ASCENDING)], unique=True, name="unique_meal_attendance"),
            IndexModel(
                [("tenant_id", ASCENDING), ("enrollment_id", ASCENDING), ("service_date", ASCENDING), ("meal_category_code", ASCENDING)],
                unique=True,
                name="unique_meal_attendance_slot",
            ),
        ]


class HostelMessBillingPeriod(Document):
    tenant_id: PydanticObjectId
    period_id: str
    mess_code: str | None = None
    label: str
    period_start: date
    period_end: date
    status: MessBillingPeriodStatus = MessBillingPeriodStatus.DRAFT
    created_by: PydanticObjectId | None = None
    approved_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_mess_billing_periods"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("period_id", ASCENDING)], unique=True, name="unique_mess_billing_period"),
            IndexModel([("tenant_id", ASCENDING), ("period_start", DESCENDING)], name="billing_periods_by_start"),
        ]


class HostelMessBillingRecord(Document):
    tenant_id: PydanticObjectId
    record_id: str
    period_id: str
    enrollment_id: str
    student_user_id: PydanticObjectId
    resident_id: str
    plan_code: str
    mess_code: str
    amount: float = Field(ge=0)
    proration_days: int | None = None
    status: MessBillingRecordStatus = MessBillingRecordStatus.DRAFT
    finance_demand_id: str | None = None
    exception_note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_mess_billing_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("record_id", ASCENDING)], unique=True, name="unique_mess_billing_record"),
            IndexModel(
                [("tenant_id", ASCENDING), ("period_id", ASCENDING), ("enrollment_id", ASCENDING)],
                unique=True,
                name="unique_billing_per_enrollment_period",
            ),
            IndexModel([("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("status", ASCENDING)], name="billing_by_student"),
        ]


class HostelMessBillingAdjustment(Document):
    tenant_id: PydanticObjectId
    adjustment_id: str
    record_id: str | None = None
    enrollment_id: str
    student_user_id: PydanticObjectId
    amount_delta: float
    reason: str
    source_type: str = "manual"
    source_ref: str | None = None
    approved_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_mess_billing_adjustments"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("adjustment_id", ASCENDING)], unique=True, name="unique_mess_billing_adj"),
        ]


class HostelMessFinanceReference(Document):
    tenant_id: PydanticObjectId
    reference_id: str
    record_id: str
    demand_id: str
    student_user_id: PydanticObjectId
    amount: float = Field(ge=0)
    synced_status: str | None = None
    last_synced_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_mess_finance_references"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("reference_id", ASCENDING)], unique=True, name="unique_mess_finance_ref"),
            IndexModel([("tenant_id", ASCENDING), ("demand_id", ASCENDING)], unique=True, name="unique_mess_demand_link"),
        ]