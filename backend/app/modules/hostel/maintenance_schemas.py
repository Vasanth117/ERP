"""Maintenance and complaints API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.modules.hostel.maintenance_models import HostelComplaintPriority, HostelComplaintStatus


class ComplaintCategoryUpsert(BaseModel):
    category_code: str
    label: str
    default_priority: HostelComplaintPriority = HostelComplaintPriority.MEDIUM
    active: bool = True


class ComplaintSubmit(BaseModel):
    hostel_code: str | None = None
    building_code: str
    block_code: str | None = None
    floor_id: str | None = None
    room_code: str
    bed_id: str | None = None
    category_code: str
    subject: str = Field(max_length=300)
    description: str = Field(max_length=4000)
    priority: HostelComplaintPriority | None = None
    attachment_refs: list[str] = Field(default_factory=list)


class ComplaintRead(BaseModel):
    complaint_id: str
    student_user_id: str | None
    hostel_code: str | None
    building_code: str
    room_code: str
    category_code: str
    subject: str
    description: str
    priority: HostelComplaintPriority
    status: HostelComplaintStatus
    assigned_to_user_id: str | None
    expected_completion: date | None
    created_at: datetime


class ComplaintAssign(BaseModel):
    complaint_id: str
    assignee_user_id: str | None = None
    department: str | None = None
    supervisor_user_id: str | None = None
    work_instructions: str | None = None
    expected_completion: date | None = None
    materials_required: list[str] = Field(default_factory=list)


class ComplaintStatusUpdate(BaseModel):
    complaint_id: str
    status: HostelComplaintStatus
    note: str | None = None
    repair_evidence_refs: list[str] = Field(default_factory=list)


class ComplaintClarification(BaseModel):
    complaint_id: str
    note: str = Field(max_length=2000)


class ComplaintFeedbackInput(BaseModel):
    complaint_id: str
    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = None
    reopen_requested: bool = False


class MaintenanceScheduleUpsert(BaseModel):
    schedule_id: str | None = None
    schedule_type: str
    title: str
    hostel_code: str | None = None
    building_code: str | None = None
    scheduled_date: date
    assignee_user_id: str | None = None


class FacilityUnavailabilityInput(BaseModel):
    complaint_id: str | None = None
    facility_type: str = Field(pattern="^(room|bed)$")
    building_code: str
    block_code: str | None = None
    room_code: str
    bed_id: str | None = None
    hostel_code: str | None = None
    unavailable: bool = True
    reason: str = Field(max_length=1000)


class MaintenanceDashboard(BaseModel):
    total_complaints: int
    new_complaints: int
    open_complaints: int
    in_progress: int
    high_priority: int
    overdue: int
    pending_assignments: int
    resolved: int
    rooms_unavailable: int