"""Examination cell — venues, seating plans and invigilation."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.examinations.exam_cell_seating_enums import (
    ExamDutyHistoryAction,
    ExamDutyHistoryKind,
    ExamInvigilatorRole,
    ExamSeatingAllocationStatus,
    ExamSeatingPlanStatus,
    ExamSeatingPolicy,
)


class ExamVenue(Document):
    tenant_id: PydanticObjectId
    venue_id: str
    exam_session_id: PydanticObjectId
    name: str
    campus_id: PydanticObjectId | None = None
    centre_code: str | None = None
    facility_id: str | None = None
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_venues"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("venue_id", ASCENDING)],
                unique=True,
                name="unique_exam_venue_id",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("exam_session_id", ASCENDING)],
                name="exam_venues_by_session",
            ),
        ]


class ExamRoom(Document):
    tenant_id: PydanticObjectId
    room_id: str
    venue_id: str
    exam_session_id: PydanticObjectId
    room_label: str
    campus_id: PydanticObjectId | None = None
    facility_id: str | None = None
    department_code: str | None = None
    programme_code: str | None = None
    total_capacity: int = Field(ge=0)
    usable_seating_capacity: int = Field(ge=0)
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_rooms"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("room_id", ASCENDING)],
                unique=True,
                name="unique_exam_room_id",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("exam_session_id", ASCENDING), ("room_label", ASCENDING)],
                unique=True,
                name="unique_exam_room_label_per_session",
            ),
            IndexModel([("tenant_id", ASCENDING), ("venue_id", ASCENDING)], name="exam_rooms_by_venue"),
        ]


class ExamSeatingPlan(Document):
    tenant_id: PydanticObjectId
    plan_id: str
    exam_session_id: PydanticObjectId
    title: str
    course_code: str | None = None
    timetable_entry_id: PydanticObjectId | None = None
    seating_policy: ExamSeatingPolicy = ExamSeatingPolicy.MIXED
    status: ExamSeatingPlanStatus = ExamSeatingPlanStatus.DRAFT
    published_at: datetime | None = None
    approved_by: PydanticObjectId | None = None
    created_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_seating_plans"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("plan_id", ASCENDING)],
                unique=True,
                name="unique_exam_seating_plan_id",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("exam_session_id", ASCENDING), ("status", ASCENDING)],
                name="exam_seating_plans_by_session",
            ),
        ]


class ExamSeatingAllocation(Document):
    tenant_id: PydanticObjectId
    allocation_id: str
    plan_id: str
    exam_session_id: PydanticObjectId
    room_id: str
    student_user_id: PydanticObjectId
    course_code: str
    seat_number: int = Field(ge=1)
    roll_number: str | None = None
    display_name: str | None = None
    department_code: str | None = None
    programme_code: str | None = None
    status: ExamSeatingAllocationStatus = ExamSeatingAllocationStatus.ALLOCATED
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_seating_allocations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("allocation_id", ASCENDING)],
                unique=True,
                name="unique_exam_seating_allocation_id",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("plan_id", ASCENDING), ("student_user_id", ASCENDING)],
                unique=True,
                name="unique_student_per_seating_plan",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("plan_id", ASCENDING), ("room_id", ASCENDING), ("seat_number", ASCENDING)],
                unique=True,
                name="unique_seat_per_room_plan",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("exam_session_id", ASCENDING), ("student_user_id", ASCENDING)],
                name="exam_seating_by_student_session",
            ),
        ]


class ExamInvigilatorAssignment(Document):
    tenant_id: PydanticObjectId
    assignment_id: str
    plan_id: str
    exam_session_id: PydanticObjectId
    room_id: str
    faculty_user_id: PydanticObjectId
    duty_role: ExamInvigilatorRole = ExamInvigilatorRole.INVIGILATOR
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_invigilator_assignments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("assignment_id", ASCENDING)],
                unique=True,
                name="unique_exam_invigilator_assignment",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("plan_id", ASCENDING), ("room_id", ASCENDING), ("faculty_user_id", ASCENDING)],
                unique=True,
                name="unique_invigilator_room_plan",
            ),
        ]


class ExamDutyHistory(Document):
    tenant_id: PydanticObjectId
    history_id: str
    kind: ExamDutyHistoryKind
    action: ExamDutyHistoryAction
    plan_id: str | None = None
    exam_session_id: PydanticObjectId | None = None
    resource_id: str | None = None
    actor_id: PydanticObjectId | None = None
    note: str | None = Field(default=None, max_length=500)
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_duty_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("history_id", ASCENDING)],
                unique=True,
                name="unique_exam_duty_history_id",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("plan_id", ASCENDING), ("created_at", DESCENDING)],
                name="exam_duty_history_plan",
            ),
        ]