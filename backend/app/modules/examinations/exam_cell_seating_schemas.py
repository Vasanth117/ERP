"""Examination cell — seating request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.modules.examinations.exam_cell_seating_enums import (
    ExamInvigilatorRole,
    ExamSeatingAllocationStatus,
    ExamSeatingPlanStatus,
    ExamSeatingPolicy,
)
from app.modules.examinations.exam_cell_seating_models import (
    ExamInvigilatorAssignment,
    ExamRoom,
    ExamSeatingAllocation,
    ExamSeatingPlan,
    ExamVenue,
)


class ExamVenueCreate(BaseModel):
    exam_session_id: str
    name: str = Field(min_length=1, max_length=120)
    campus_id: str | None = None
    centre_code: str | None = None
    facility_id: str | None = None

    @field_validator("centre_code")
    @classmethod
    def normalize_centre(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else None


class ExamVenueRead(BaseModel):
    id: str
    venue_id: str
    exam_session_id: str
    name: str
    campus_id: str | None
    centre_code: str | None
    facility_id: str | None
    active: bool

    @classmethod
    def from_doc(cls, doc: ExamVenue) -> "ExamVenueRead":
        return cls(
            id=str(doc.id),
            venue_id=doc.venue_id,
            exam_session_id=str(doc.exam_session_id),
            name=doc.name,
            campus_id=str(doc.campus_id) if doc.campus_id else None,
            centre_code=doc.centre_code,
            facility_id=doc.facility_id,
            active=doc.active,
        )


class ExamRoomCreate(BaseModel):
    venue_id: str
    room_label: str = Field(min_length=1, max_length=40)
    facility_id: str | None = None
    campus_id: str | None = None
    department_code: str | None = None
    programme_code: str | None = None
    total_capacity: int = Field(ge=0)
    usable_seating_capacity: int = Field(ge=0)

    @field_validator("room_label", "department_code", "programme_code")
    @classmethod
    def upper_trim(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else None


class ExamRoomRead(BaseModel):
    id: str
    room_id: str
    venue_id: str
    exam_session_id: str
    room_label: str
    total_capacity: int
    usable_seating_capacity: int
    department_code: str | None
    programme_code: str | None

    @classmethod
    def from_doc(cls, doc: ExamRoom) -> "ExamRoomRead":
        return cls(
            id=str(doc.id),
            room_id=doc.room_id,
            venue_id=doc.venue_id,
            exam_session_id=str(doc.exam_session_id),
            room_label=doc.room_label,
            total_capacity=doc.total_capacity,
            usable_seating_capacity=doc.usable_seating_capacity,
            department_code=doc.department_code,
            programme_code=doc.programme_code,
        )


class ExamSeatingPlanCreate(BaseModel):
    exam_session_id: str
    title: str = Field(min_length=1, max_length=160)
    course_code: str | None = None
    timetable_entry_id: str | None = None
    seating_policy: ExamSeatingPolicy = ExamSeatingPolicy.MIXED

    @field_validator("course_code")
    @classmethod
    def normalize_course(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else None


class ExamSeatingPlanRead(BaseModel):
    id: str
    plan_id: str
    exam_session_id: str
    title: str
    course_code: str | None
    seating_policy: ExamSeatingPolicy
    status: ExamSeatingPlanStatus
    published_at: datetime | None

    @classmethod
    def from_doc(cls, doc: ExamSeatingPlan) -> "ExamSeatingPlanRead":
        return cls(
            id=str(doc.id),
            plan_id=doc.plan_id,
            exam_session_id=str(doc.exam_session_id),
            title=doc.title,
            course_code=doc.course_code,
            seating_policy=doc.seating_policy,
            status=doc.status,
            published_at=doc.published_at,
        )


class ExamSeatingAllocateRequest(BaseModel):
    plan_id: str
    course_code: str | None = None

    @field_validator("course_code")
    @classmethod
    def normalize_course(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else None


class ExamSeatingAllocationRead(BaseModel):
    allocation_id: str
    plan_id: str
    room_id: str
    student_user_id: str
    course_code: str
    seat_number: int
    roll_number: str | None
    display_name: str | None
    status: ExamSeatingAllocationStatus

    @classmethod
    def from_doc(cls, doc: ExamSeatingAllocation) -> "ExamSeatingAllocationRead":
        return cls(
            allocation_id=doc.allocation_id,
            plan_id=doc.plan_id,
            room_id=doc.room_id,
            student_user_id=str(doc.student_user_id),
            course_code=doc.course_code,
            seat_number=doc.seat_number,
            roll_number=doc.roll_number,
            display_name=doc.display_name,
            status=doc.status,
        )


class ExamSeatingChangeRequest(BaseModel):
    room_id: str
    seat_number: int = Field(ge=1)
    note: str | None = Field(default=None, max_length=300)


class ExamInvigilatorAssignRequest(BaseModel):
    plan_id: str
    room_id: str
    faculty_user_id: str
    duty_role: ExamInvigilatorRole = ExamInvigilatorRole.INVIGILATOR
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None


class ExamInvigilatorAssignmentRead(BaseModel):
    assignment_id: str
    plan_id: str
    room_id: str
    faculty_user_id: str
    duty_role: ExamInvigilatorRole
    scheduled_start: datetime | None
    scheduled_end: datetime | None
    active: bool

    @classmethod
    def from_doc(cls, doc: ExamInvigilatorAssignment) -> "ExamInvigilatorAssignmentRead":
        return cls(
            assignment_id=doc.assignment_id,
            plan_id=doc.plan_id,
            room_id=doc.room_id,
            faculty_user_id=str(doc.faculty_user_id),
            duty_role=doc.duty_role,
            scheduled_start=doc.scheduled_start,
            scheduled_end=doc.scheduled_end,
            active=doc.active,
        )


class ExamRoomAttendanceRow(BaseModel):
    seat_number: int
    student_user_id: str
    roll_number: str | None
    display_name: str | None
    course_code: str


class ExamRoomAttendanceSheet(BaseModel):
    plan_id: str
    room_id: str
    room_label: str
    rows: list[ExamRoomAttendanceRow]


class ExamSeatingPlanSummary(BaseModel):
    plan_id: str
    allocated_students: int
    total_usable_capacity: int
    rooms_used: int