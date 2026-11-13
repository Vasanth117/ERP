"""Read authoritative academic and operational data for student dashboards."""

from datetime import date, datetime, timedelta, timezone

from beanie import PydanticObjectId

from app.modules.academics.curriculum_models import EnrollmentRosterEntry
from app.modules.academics.models import (
    AcademicCalendarEvent,
    AcademicYearContext,
    ExaminationSchedule,
    TimetableEntry,
)
from app.modules.attendance.enums import AttendanceMarkStatus
from app.modules.attendance.models import AttendancePolicyReference, AttendanceRecord, AttendanceSession
from app.modules.examinations.enums import StudentMarkStatus
from app.modules.examinations.models import StudentAssessmentMark
from app.modules.faculty.communication_models import CommunicationRecipient, FacultyAnnouncement
from app.modules.lms.enums import LmsAssignmentStatus, SubmissionStatus
from app.modules.lms.models import AssignmentSubmission, CourseAssignment


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def resolve_date_window(*, anchor: date | None, range_key: str) -> tuple[datetime, datetime]:
    base = anchor or date.today()
    start = datetime.combine(base, datetime.min.time(), tzinfo=timezone.utc)
    if range_key == "today":
        end = start + timedelta(days=1)
    elif range_key == "month":
        end = start + timedelta(days=31)
    else:
        end = start + timedelta(days=7)
    return start, end


class StudentDataReader:
    async def current_academic_context(self, tenant_id: PydanticObjectId) -> AcademicYearContext | None:
        return await AcademicYearContext.find_one({"tenant_id": tenant_id, "is_current": True})

    async def roster_entries(
        self,
        tenant_id: PydanticObjectId,
        student_user_id: PydanticObjectId,
        *,
        academic_year_label: str | None = None,
        semester_label: str | None = None,
    ) -> list[EnrollmentRosterEntry]:
        filters: dict = {"tenant_id": tenant_id, "student_user_id": student_user_id}
        if academic_year_label:
            filters["academic_year_label"] = academic_year_label
        if semester_label:
            filters["semester_label"] = semester_label
        return await EnrollmentRosterEntry.find(filters).sort("course_code").to_list()

    async def timetable_for_student(
        self,
        tenant_id: PydanticObjectId,
        student_user_id: PydanticObjectId,
        *,
        academic_year_label: str,
        semester_label: str,
        day_of_week: int | None = None,
    ) -> list[TimetableEntry]:
        roster = await self.roster_entries(
            tenant_id,
            student_user_id,
            academic_year_label=academic_year_label,
            semester_label=semester_label,
        )
        if not roster:
            return []
        or_clauses = [{"course_code": r.course_code, "section": r.section_code} for r in roster]
        filters: dict = {
            "tenant_id": tenant_id,
            "academic_year_label": academic_year_label,
            "semester_label": semester_label,
            "$or": or_clauses,
        }
        if day_of_week is not None:
            filters["day_of_week"] = day_of_week
        return await TimetableEntry.find(filters).sort([("day_of_week", 1), ("start_time", 1)]).to_list()

    async def examination_schedule(
        self,
        tenant_id: PydanticObjectId,
        student_user_id: PydanticObjectId,
        *,
        academic_year_label: str,
        semester_label: str,
        from_time: datetime | None = None,
        limit: int = 20,
    ) -> list[ExaminationSchedule]:
        roster = await self.roster_entries(
            tenant_id,
            student_user_id,
            academic_year_label=academic_year_label,
            semester_label=semester_label,
        )
        course_codes = {r.course_code for r in roster}
        section_by_course = {r.course_code: r.section_code for r in roster}
        if not course_codes:
            return []
        rows = await ExaminationSchedule.find(
            {
                "tenant_id": tenant_id,
                "academic_year_label": academic_year_label,
                "semester_label": semester_label,
                "course_code": {"$in": list(course_codes)},
            }
        ).sort("scheduled_at").limit(limit * 3).to_list()
        if from_time is not None:
            rows = [row for row in rows if row.scheduled_at >= from_time]
        filtered: list[ExaminationSchedule] = []
        for row in rows:
            if row.section is not None and row.section != section_by_course.get(row.course_code):
                continue
            filtered.append(row)
            if len(filtered) >= limit:
                break
        return filtered

    async def attendance_summary(
        self,
        tenant_id: PydanticObjectId,
        student_user_id: PydanticObjectId,
        *,
        academic_year_label: str,
        semester_label: str,
    ) -> dict:
        roster = await self.roster_entries(
            tenant_id,
            student_user_id,
            academic_year_label=academic_year_label,
            semester_label=semester_label,
        )
        if not roster:
            return {"status": "not_enrolled", "courses": [], "overall_percentage": None}
        policy = await AttendancePolicyReference.find_one({"tenant_id": tenant_id, "is_active": True})
        min_required = policy.rules.min_percentage_required if policy else 75.0
        course_summaries: list[dict] = []
        total_weight = 0.0
        total_sessions = 0
        for entry in roster:
            sessions = await AttendanceSession.find(
                {
                    "tenant_id": tenant_id,
                    "course_code": entry.course_code,
                    "section": entry.section_code,
                    "academic_year_label": academic_year_label,
                    "semester_label": semester_label,
                }
            ).to_list()
            session_ids = [s.id for s in sessions]
            if not session_ids:
                course_summaries.append(
                    {
                        "course_code": entry.course_code,
                        "section": entry.section_code,
                        "percentage": None,
                        "sessions_held": 0,
                        "min_required": min_required,
                    }
                )
                continue
            records = await AttendanceRecord.find(
                {"tenant_id": tenant_id, "student_user_id": student_user_id, "session_id": {"$in": session_ids}}
            ).to_list()
            held = len(sessions)
            present = sum(1 for r in records if r.status == AttendanceMarkStatus.PRESENT)
            late = sum(1 for r in records if r.status == AttendanceMarkStatus.LATE)
            excused = sum(1 for r in records if r.status == AttendanceMarkStatus.EXCUSED)
            attended = present + late + excused
            pct = round((attended / held) * 100, 2) if held else None
            course_summaries.append(
                {
                    "course_code": entry.course_code,
                    "section": entry.section_code,
                    "percentage": pct,
                    "sessions_held": held,
                    "min_required": min_required,
                }
            )
            total_sessions += held
            total_weight += attended
        overall = round((total_weight / total_sessions) * 100, 2) if total_sessions else None
        return {
            "status": "available",
            "courses": course_summaries,
            "overall_percentage": overall,
            "min_required": min_required,
        }

    async def pending_assignments(
        self,
        tenant_id: PydanticObjectId,
        student_user_id: PydanticObjectId,
        *,
        academic_year_label: str,
        semester_label: str,
        limit: int = 30,
    ) -> list[CourseAssignment]:
        roster = await self.roster_entries(
            tenant_id,
            student_user_id,
            academic_year_label=academic_year_label,
            semester_label=semester_label,
        )
        if not roster:
            return []
        or_clauses = [{"course_code": r.course_code, "section": r.section_code} for r in roster]
        assignments = (
            await CourseAssignment.find(
                {
                    "tenant_id": tenant_id,
                    "academic_year_label": academic_year_label,
                    "semester_label": semester_label,
                    "status": LmsAssignmentStatus.PUBLISHED,
                    "$or": or_clauses,
                }
            )
            .sort("deadline_at")
            .limit(limit * 2)
            .to_list()
        )
        pending: list[CourseAssignment] = []
        for item in assignments:
            submitted = await AssignmentSubmission.find_one(
                {
                    "tenant_id": tenant_id,
                    "assignment_id": item.id,
                    "student_user_id": student_user_id,
                    "status": {
                        "$in": [
                            SubmissionStatus.SUBMITTED,
                            SubmissionStatus.LATE,
                            SubmissionStatus.EVALUATED,
                        ]
                    },
                }
            )
            if submitted is None:
                pending.append(item)
            if len(pending) >= limit:
                break
        return pending

    async def published_results(
        self, tenant_id: PydanticObjectId, student_user_id: PydanticObjectId, *, limit: int = 50
    ) -> list[StudentAssessmentMark]:
        return (
            await StudentAssessmentMark.find(
                {
                    "tenant_id": tenant_id,
                    "student_user_id": student_user_id,
                    "status": StudentMarkStatus.APPROVED,
                }
            )
            .sort("-updated_at")
            .limit(limit)
            .to_list()
        )

    async def academic_notifications(
        self, tenant_id: PydanticObjectId, student_user_id: PydanticObjectId, *, limit: int = 20
    ) -> list[dict]:
        recipients = (
            await CommunicationRecipient.find({"tenant_id": tenant_id, "student_user_id": student_user_id})
            .sort("-created_at")
            .limit(limit)
            .to_list()
        )
        if not recipients:
            return []
        announcement_ids = [r.announcement_id for r in recipients]
        announcements = await FacultyAnnouncement.find({"_id": {"$in": announcement_ids}, "status": "published"}).to_list()
        by_id = {a.id: a for a in announcements}
        items: list[dict] = []
        for rec in recipients:
            ann = by_id.get(rec.announcement_id)
            if ann is None:
                continue
            items.append(
                {
                    "id": str(ann.id),
                    "title": ann.title,
                    "body": ann.body[:500],
                    "course_code": ann.course_code,
                    "created_at": ann.created_at,
                }
            )
        return items[:limit]

    async def academic_deadlines(
        self,
        tenant_id: PydanticObjectId,
        *,
        from_time: datetime | None = None,
        limit: int = 20,
    ) -> list[AcademicCalendarEvent]:
        filters: dict = {
            "tenant_id": tenant_id,
            "audience": {"$in": ["students", "all", "student"]},
        }
        if from_time is not None:
            filters["event_at"] = {"$gte": from_time}
        return await AcademicCalendarEvent.find(filters).sort("event_at").limit(limit).to_list()
