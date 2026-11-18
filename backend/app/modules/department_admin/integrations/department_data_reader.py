"""Read institutional data scoped to one department (central department id)."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timezone
from typing import Any

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.common.roles import Role
from app.modules.academics.models import (
    AcademicCalendarEvent,
    AcademicYearContext,
    ExaminationSchedule,
    PendingAssignmentEvaluation,
    PendingAttendanceSubmission,
    TimetableEntry,
    UpcomingAssessment,
)
from app.modules.attendance.enums import AttendanceCorrectionStatus, AttendanceSessionStatus
from app.modules.attendance.models import AttendanceCorrectionRequest, AttendanceSession
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicProgramme
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.faculty.models import FacultyProfile
from app.modules.hr.enums import LeaveRequestStatus
from app.modules.hr.models import LeaveRequest
from app.modules.students.enums import AcademicStanding
from app.modules.students.models import StudentAcademicRecord, StudentActivityLog, StudentProfile
from app.modules.tenants.models import Tenant


class DepartmentDataReader:
    def __init__(self) -> None:
        self._college = OperationalDataReader()

    async def _faculty_user_ids(self, tenant_id: PydanticObjectId, central_department_id: PydanticObjectId) -> list[PydanticObjectId]:
        rows = await FacultyProfile.find(
            Eq(FacultyProfile.tenant_id, tenant_id),
            Eq(FacultyProfile.department_id, central_department_id),
        ).to_list()
        if rows:
            return [r.user_id for r in rows]
        users = await User.find(
            Eq(User.tenant_id, tenant_id),
            Eq(User.role, Role.FACULTY),
            Eq(User.department_id, central_department_id),
            Eq(User.is_active, True),
        ).to_list()
        return [u.id for u in users]

    def _student_profile_filters(
        self,
        tenant_id: PydanticObjectId,
        central_department_id: PydanticObjectId,
        *,
        programme_code: str | None = None,
        batch_label: str | None = None,
        section_code: str | None = None,
    ) -> dict[str, Any]:
        filters: dict[str, Any] = {"tenant_id": tenant_id, "department_id": central_department_id}
        if programme_code:
            filters["programme_code"] = programme_code.upper()
        if batch_label:
            filters["batch_label"] = batch_label
        if section_code:
            filters["section_code"] = section_code
        return filters

    async def student_statistics(
        self,
        tenant_id: PydanticObjectId,
        central_department_id: PydanticObjectId,
        *,
        programme_code: str | None = None,
        batch_label: str | None = None,
        section_code: str | None = None,
    ) -> dict[str, Any]:
        base = self._student_profile_filters(
            tenant_id,
            central_department_id,
            programme_code=programme_code,
            batch_label=batch_label,
            section_code=section_code,
        )
        total = await StudentProfile.find(base).count()
        active = await User.find(
            Eq(User.tenant_id, tenant_id),
            Eq(User.role, Role.STUDENT),
            Eq(User.department_id, central_department_id),
            Eq(User.is_active, True),
        ).count()
        inactive = max(total - active, 0)
        coll = StudentProfile.get_motor_collection()
        by_programme = await coll.aggregate(
            [
                {"$match": base},
                {"$group": {"_id": "$programme_code", "count": {"$sum": 1}}},
            ]
        ).to_list(length=200)
        by_batch = await coll.aggregate(
            [
                {"$match": base},
                {"$group": {"_id": "$batch_label", "count": {"$sum": 1}}},
            ]
        ).to_list(length=200)
        by_section = await coll.aggregate(
            [
                {"$match": base},
                {"$group": {"_id": "$section_code", "count": {"$sum": 1}}},
            ]
        ).to_list(length=200)
        student_users = await User.find(
            Eq(User.tenant_id, tenant_id),
            Eq(User.role, Role.STUDENT),
            Eq(User.department_id, central_department_id),
        ).limit(5000).to_list()
        student_user_ids = [u.id for u in student_users]
        follow_up = 0
        if student_user_ids:
            follow_up = await StudentAcademicRecord.find(
                {
                    "tenant_id": tenant_id,
                    "user_id": {"$in": student_user_ids},
                    "academic_standing": {
                        "$in": [AcademicStanding.PROBATION.value, AcademicStanding.SUSPENDED.value],
                    },
                }
            ).count()
        return {
            "total_enrolled": total,
            "active_students": active,
            "inactive_students": inactive,
            "by_programme": [{"code": row["_id"], "count": row["count"]} for row in by_programme if row["_id"]],
            "by_batch": [{"label": row["_id"], "count": row["count"]} for row in by_batch if row["_id"]],
            "by_section": [{"code": row["_id"], "count": row["count"]} for row in by_section if row["_id"]],
            "new_admissions_count": None,
            "follow_up_count": follow_up,
        }

    async def faculty_statistics(self, tenant_id: PydanticObjectId, central_department_id: PydanticObjectId) -> dict[str, Any]:
        faculty_ids = await self._faculty_user_ids(tenant_id, central_department_id)
        total = len(faculty_ids)
        active = await User.find(
            Eq(User.tenant_id, tenant_id),
            In(User.id, faculty_ids) if faculty_ids else Eq(User.id, PydanticObjectId()),
            Eq(User.is_active, True),
        ).count() if faculty_ids else 0
        on_leave = 0
        if faculty_ids:
            on_leave = await LeaveRequest.find(
                Eq(LeaveRequest.tenant_id, tenant_id),
                In(LeaveRequest.employee_user_id, faculty_ids),
                Eq(LeaveRequest.status, LeaveRequestStatus.APPROVED),
            ).count()
        profiles = await FacultyProfile.find(
            Eq(FacultyProfile.tenant_id, tenant_id),
            Eq(FacultyProfile.department_id, central_department_id),
        ).to_list()
        designations = Counter(p.designation or "unspecified" for p in profiles)
        unassigned = sum(1 for p in profiles if not p.specialization)
        return {
            "total_faculty": total,
            "active_faculty": active,
            "on_approved_leave": on_leave,
            "by_designation": [{"designation": k, "count": v} for k, v in designations.items()],
            "unassigned_teaching_count": unassigned,
            "workload_summary_available": total > 0,
        }

    async def academic_summary(
        self,
        tenant_id: PydanticObjectId,
        programme_codes: list[str],
        *,
        academic_year_label: str | None,
        semester_label: str | None,
    ) -> dict[str, Any]:
        programme_filters: dict[str, Any] = {"tenant_id": tenant_id}
        if programme_codes:
            programme_filters["programme_code"] = {"$in": [c.upper() for c in programme_codes]}
        programme_count = await AcademicProgramme.find(programme_filters).count()
        subject_offerings = None
        curriculum_coverage = None
        return {
            "active_programmes": programme_count,
            "programme_codes": programme_codes,
            "current_academic_year": academic_year_label,
            "current_semester": semester_label,
            "subjects_offered_count": subject_offerings,
            "curriculum_coverage": curriculum_coverage,
            "curriculum_coverage_note": "Coverage metrics require college-defined rules; not computed in Phase 1.",
        }

    async def attendance_overview(
        self,
        tenant_id: PydanticObjectId,
        central_department_id: PydanticObjectId,
    ) -> dict[str, Any]:
        faculty_ids = await self._faculty_user_ids(tenant_id, central_department_id)
        if not faculty_ids:
            return {
                "sessions_submitted": 0,
                "pending_submissions": 0,
                "correction_requests_open": 0,
                "missing_submission_count": 0,
            }
        submitted = await AttendanceSession.find(
            Eq(AttendanceSession.tenant_id, tenant_id),
            In(AttendanceSession.faculty_user_id, faculty_ids),
            Eq(AttendanceSession.status, AttendanceSessionStatus.SUBMITTED),
        ).count()
        pending = await PendingAttendanceSubmission.find(
            Eq(PendingAttendanceSubmission.tenant_id, tenant_id),
            In(PendingAttendanceSubmission.faculty_user_id, faculty_ids),
        ).count()
        corrections = await AttendanceCorrectionRequest.find(
            Eq(AttendanceCorrectionRequest.tenant_id, tenant_id),
            Eq(AttendanceCorrectionRequest.status, AttendanceCorrectionStatus.PENDING),
        ).count()
        return {
            "sessions_submitted": submitted,
            "pending_submissions": pending,
            "correction_requests_open": corrections,
            "missing_submission_count": pending,
        }

    async def timetable_overview(
        self,
        tenant_id: PydanticObjectId,
        central_department_id: PydanticObjectId,
        *,
        anchor: date,
    ) -> dict[str, Any]:
        faculty_ids = await self._faculty_user_ids(tenant_id, central_department_id)
        if not faculty_ids:
            return {"today_sessions": [], "upcoming_sessions": [], "scheduling_conflicts": None}
        weekday = anchor.weekday()
        today_entries = await TimetableEntry.find(
            Eq(TimetableEntry.tenant_id, tenant_id),
            In(TimetableEntry.faculty_user_id, faculty_ids),
            Eq(TimetableEntry.day_of_week, weekday),
        ).sort("+start_time").limit(50).to_list()
        today_sessions = [
            {
                "course_code": e.course_code,
                "section": e.section,
                "start_time": e.start_time.isoformat(),
                "end_time": e.end_time.isoformat(),
                "room": e.room,
                "faculty_user_id": str(e.faculty_user_id),
            }
            for e in today_entries
        ]
        return {
            "today_sessions": today_sessions,
            "upcoming_sessions": today_sessions,
            "scheduling_conflicts": None,
        }

    async def examination_overview(
        self,
        tenant_id: PydanticObjectId,
        central_department_id: PydanticObjectId,
        *,
        academic_year_label: str | None,
        semester_label: str | None,
    ) -> dict[str, Any]:
        faculty_ids = await self._faculty_user_ids(tenant_id, central_department_id)
        exam_query: dict[str, Any] = {"tenant_id": tenant_id}
        if academic_year_label:
            exam_query["academic_year_label"] = academic_year_label
        if semester_label:
            exam_query["semester_label"] = semester_label
        if faculty_ids:
            exam_query["faculty_user_id"] = {"$in": faculty_ids}
        scheduled = await ExaminationSchedule.find(exam_query).count()
        pending_eval = 0
        if faculty_ids:
            pending_eval = await PendingAssignmentEvaluation.find(
                Eq(PendingAssignmentEvaluation.tenant_id, tenant_id),
                In(PendingAssignmentEvaluation.faculty_user_id, faculty_ids),
            ).count()
        upcoming = 0
        if faculty_ids:
            upcoming = await UpcomingAssessment.find(
                Eq(UpcomingAssessment.tenant_id, tenant_id),
                In(UpcomingAssessment.faculty_user_id, faculty_ids),
            ).count()
        return {
            "scheduled_examinations": scheduled,
            "pending_marks_evaluations": pending_eval,
            "upcoming_assessments": upcoming,
        }

    async def batch_section_summary(
        self,
        tenant_id: PydanticObjectId,
        central_department_id: PydanticObjectId,
    ) -> dict[str, int]:
        coll = StudentProfile.get_motor_collection()
        batches = await coll.distinct("batch_label", {"tenant_id": tenant_id, "department_id": central_department_id})
        sections = await coll.distinct("section_code", {"tenant_id": tenant_id, "department_id": central_department_id})
        return {
            "batch_count": len([b for b in batches if b]),
            "section_count": len([s for s in sections if s]),
        }

    async def department_alerts(
        self,
        tenant_id: PydanticObjectId,
        central_department_id: PydanticObjectId,
        *,
        limit: int = 30,
    ) -> list[dict[str, Any]]:
        faculty_ids = await self._faculty_user_ids(tenant_id, central_department_id)
        alerts: list[dict[str, Any]] = []
        if faculty_ids:
            for row in await PendingAttendanceSubmission.find(
                Eq(PendingAttendanceSubmission.tenant_id, tenant_id),
                In(PendingAttendanceSubmission.faculty_user_id, faculty_ids),
            ).limit(limit).to_list():
                alerts.append(
                    {
                        "category": "missing_attendance",
                        "title": f"Missing attendance — {row.class_label} {row.section}",
                        "reference_id": str(row.id),
                        "api_reference": f"/api/v1/department/dashboard/attendance",
                        "severity": "warning",
                        "occurred_at": row.created_at,
                    }
                )
            for row in await PendingAssignmentEvaluation.find(
                Eq(PendingAssignmentEvaluation.tenant_id, tenant_id),
                In(PendingAssignmentEvaluation.faculty_user_id, faculty_ids),
            ).limit(limit).to_list():
                alerts.append(
                    {
                        "category": "pending_marks",
                        "title": f"Pending marks — {row.course_code}",
                        "reference_id": str(row.id),
                        "api_reference": f"/api/v1/department/dashboard/examinations",
                        "severity": "warning",
                        "occurred_at": row.due_at,
                    }
                )
        alerts.sort(key=lambda a: a["occurred_at"] or datetime.now(timezone.utc), reverse=True)
        return alerts[:limit]

    async def department_activities(
        self,
        tenant_id: PydanticObjectId,
        central_department_id: PydanticObjectId,
        *,
        limit: int,
        skip: int,
    ) -> tuple[list[dict[str, Any]], int]:
        student_users = await User.find(
            Eq(User.tenant_id, tenant_id),
            Eq(User.role, Role.STUDENT),
            Eq(User.department_id, central_department_id),
        ).limit(500).to_list()
        student_ids = [u.id for u in student_users]
        if not student_ids:
            return [], 0
        query = StudentActivityLog.find(
            Eq(StudentActivityLog.tenant_id, tenant_id),
            In(StudentActivityLog.user_id, student_ids),
        )
        total = await query.count()
        rows = await query.sort("-created_at").skip(skip).limit(limit).to_list()
        items = [
            {
                "activity_type": row.activity_type.value,
                "summary": row.title,
                "user_id": str(row.user_id),
                "occurred_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
        return items, total

    async def current_academic_term(self, tenant_id: PydanticObjectId) -> tuple[str | None, str | None]:
        return await self._college.current_academic_term(tenant_id)

    async def upcoming_department_events(
        self,
        tenant_id: PydanticObjectId,
        central_department_id: PydanticObjectId,
        *,
        from_time: datetime,
        to_time: datetime,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        rows = await AcademicCalendarEvent.find(
            {
                "tenant_id": tenant_id,
                "event_at": {"$gte": from_time, "$lte": to_time},
                "$or": [
                    {"department_id": central_department_id},
                    {"department_id": None},
                ],
            }
        ).sort("+event_at").limit(limit).to_list()
        return [
            {
                "title": row.title,
                "event_type": row.event_type,
                "event_at": row.event_at.isoformat(),
            }
            for row in rows
        ]

    async def college_name(self, tenant_id: PydanticObjectId) -> str:
        tenant = await Tenant.get(tenant_id)
        return tenant.name if tenant else "College"