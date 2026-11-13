"""Read authoritative academic data for faculty dashboards."""

from datetime import date, datetime, timedelta, timezone

from beanie import PydanticObjectId

from app.modules.academics.models import (
    AcademicEvent,
    AcademicYearContext,
    PendingAssignmentEvaluation,
    PendingAttendanceSubmission,
    TimetableEntry,
    UpcomingAssessment,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AcademicDataReader:
    async def current_academic_context(self, tenant_id: PydanticObjectId) -> AcademicYearContext | None:
        return await AcademicYearContext.find_one({"tenant_id": tenant_id, "is_current": True})

    async def timetable_for_faculty(
        self,
        tenant_id: PydanticObjectId,
        faculty_user_id: PydanticObjectId,
        *,
        day_of_week: int | None = None,
    ) -> list[TimetableEntry]:
        filters: dict = {"tenant_id": tenant_id, "faculty_user_id": faculty_user_id}
        if day_of_week is not None:
            filters["day_of_week"] = day_of_week
        return await TimetableEntry.find(filters).sort("start_time").to_list()

    async def weekly_timetable(
        self, tenant_id: PydanticObjectId, faculty_user_id: PydanticObjectId
    ) -> list[TimetableEntry]:
        return await self.timetable_for_faculty(tenant_id, faculty_user_id)

    async def pending_attendance(
        self, tenant_id: PydanticObjectId, faculty_user_id: PydanticObjectId
    ) -> list[PendingAttendanceSubmission]:
        return (
            await PendingAttendanceSubmission.find(
                {"tenant_id": tenant_id, "faculty_user_id": faculty_user_id, "status": "pending"}
            )
            .sort("due_at")
            .to_list()
        )

    async def upcoming_assessments(
        self,
        tenant_id: PydanticObjectId,
        faculty_user_id: PydanticObjectId,
        *,
        from_time: datetime | None = None,
        limit: int = 20,
    ) -> list[UpcomingAssessment]:
        filters: dict = {"tenant_id": tenant_id, "faculty_user_id": faculty_user_id}
        if from_time is not None:
            filters["scheduled_at"] = {"$gte": from_time}
        return await UpcomingAssessment.find(filters).sort("scheduled_at").limit(limit).to_list()

    async def pending_evaluations(
        self, tenant_id: PydanticObjectId, faculty_user_id: PydanticObjectId
    ) -> list[PendingAssignmentEvaluation]:
        return (
            await PendingAssignmentEvaluation.find({"tenant_id": tenant_id, "faculty_user_id": faculty_user_id})
            .sort("due_at")
            .to_list()
        )

    async def academic_events(
        self,
        tenant_id: PydanticObjectId,
        *,
        department_id: PydanticObjectId | None,
        from_time: datetime | None = None,
        limit: int = 10,
    ) -> list[AcademicEvent]:
        filters: dict = {"tenant_id": tenant_id, "audience": {"$in": ["faculty", "all"]}}
        if department_id is not None:
            filters["$or"] = [{"department_id": department_id}, {"department_id": None}]
        if from_time is not None:
            filters["event_at"] = {"$gte": from_time}
        return await AcademicEvent.find(filters).sort("event_at").limit(limit).to_list()


def resolve_date_window(
    *,
    anchor: date | None,
    range_key: str,
) -> tuple[datetime, datetime]:
    base = anchor or date.today()
    start = datetime.combine(base, datetime.min.time(), tzinfo=timezone.utc)
    if range_key == "today":
        end = start + timedelta(days=1)
    elif range_key == "month":
        end = start + timedelta(days=30)
    else:
        end = start + timedelta(days=7)
    return start, end
