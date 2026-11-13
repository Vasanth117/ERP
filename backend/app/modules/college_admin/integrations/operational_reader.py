"""Read authoritative tenant data for college admin dashboards."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.common.roles import Role
from app.modules.academics.models import AcademicCalendarEvent, AcademicYearContext, PendingAssignmentEvaluation
from app.modules.attendance.enums import AttendanceCorrectionStatus, AttendanceSessionStatus
from app.modules.attendance.models import AttendanceCorrectionRequest, AttendanceSession
from app.modules.auth.models import User
from app.modules.college_admin.enums import DashboardDateRange, PendingApprovalCategory
from app.modules.college_admin.schemas import (
    ActivitySummary,
    AttendanceDashboardSummary,
    ExaminationDashboardSummary,
    FinanceDashboardSummary,
    HeadcountStatistics,
    IntegrationHealthSummary,
    LibraryHostelSummary,
    NotificationSummary,
    PendingApprovalItem,
    SupportRequestSummary,
)
from app.modules.examinations.examination_registration_enums import SemesterResultPublicationStatus
from app.modules.examinations.result_publication_models import SemesterResultPublication
from app.modules.faculty.models import FacultyActivityLog, FacultyProfile
from app.modules.finance.finance_enums import FeeDemandStatus, PaymentTransactionStatus
from app.modules.finance.finance_models import PaymentTransaction, StudentFeeDemand
from app.modules.hostel.hostel_enums import HostelApplicationStatus
from app.modules.hostel.hostel_models import HostelApplication, HostelRoomAllocation
from app.modules.hr.enums import LeaveRequestStatus
from app.modules.hr.models import EmployeeProfileSnapshot, LeaveRequest
from app.modules.integrations.enums import IntegrationScope
from app.modules.integrations.models import IntegrationConfiguration, IntegrationHealth
from app.modules.library.library_enums import LibraryCirculationStatus, LibraryFineStatus
from app.modules.library.library_models import LibraryCatalogItem, LibraryCirculation, LibraryFine
from app.modules.students.enums import StudentAcademicRequestStatus
from app.modules.students.student_portal_enums import StudentDocumentRequestStatus, StudentServiceRequestStatus
from app.modules.students.models import StudentAcademicRequest, StudentActivityLog, StudentProfile
from app.modules.students.student_portal_models import StudentProfileCorrectionRequest, StudentServiceRequest
from app.modules.tenants.models import Department
from app.modules.academics.models import ExaminationSchedule, PendingAttendanceSubmission


def _date_window(anchor: date, range_key: DashboardDateRange) -> tuple[datetime, datetime]:
    anchor_dt = datetime.combine(anchor, datetime.min.time(), tzinfo=timezone.utc)
    if range_key == DashboardDateRange.TODAY:
        return anchor_dt, anchor_dt + timedelta(days=1)
    if range_key == DashboardDateRange.WEEK:
        start = anchor_dt - timedelta(days=anchor.weekday())
        return start, start + timedelta(days=7)
    if range_key == DashboardDateRange.MONTH:
        start = anchor_dt.replace(day=1)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)
        return start, end
    return anchor_dt - timedelta(days=120), anchor_dt + timedelta(days=1)


class OperationalDataReader:
    async def current_academic_term(self, tenant_id: PydanticObjectId) -> tuple[str | None, str | None]:
        ctx = await AcademicYearContext.find_one(
            Eq(AcademicYearContext.tenant_id, tenant_id),
            Eq(AcademicYearContext.is_current, True),
        )
        if ctx is None:
            return None, None
        return ctx.academic_year_label, ctx.semester_label

    async def headcount_statistics(
        self,
        tenant_id: PydanticObjectId,
        *,
        department_id: PydanticObjectId | None = None,
    ) -> HeadcountStatistics:
        student_filters: dict[str, Any] = {"tenant_id": tenant_id}
        if department_id is not None:
            student_filters["department_id"] = department_id

        total_students = await StudentProfile.find(student_filters).count()
        active_students = await User.find(
            Eq(User.tenant_id, tenant_id),
            Eq(User.role, Role.STUDENT),
            Eq(User.is_active, True),
        ).count()
        if department_id is not None:
            active_students = await User.find(
                Eq(User.tenant_id, tenant_id),
                Eq(User.role, Role.STUDENT),
                Eq(User.is_active, True),
                Eq(User.department_id, department_id),
            ).count()

        faculty_count = await FacultyProfile.find(
            Eq(FacultyProfile.tenant_id, tenant_id),
        ).count()
        employee_count = await EmployeeProfileSnapshot.find(
            Eq(EmployeeProfileSnapshot.tenant_id, tenant_id),
        ).count()
        if employee_count == 0:
            employee_count = await User.find(
                Eq(User.tenant_id, tenant_id),
                In(User.role, [Role.FACULTY, Role.HR_STAFF, Role.ACCOUNTS_STAFF, Role.FINANCE_STAFF]),
                Eq(User.is_active, True),
            ).count()

        department_count = await Department.find(Eq(Department.tenant_id, tenant_id), Eq(Department.is_active, True)).count()

        programmes = await StudentProfile.get_motor_collection().distinct(
            "programme_code",
            {"tenant_id": tenant_id, "programme_code": {"$ne": None}},
        )
        programme_count = len([p for p in programmes if p])

        return HeadcountStatistics(
            total_students=total_students,
            active_students=active_students,
            faculty_count=faculty_count,
            employee_count=employee_count,
            department_count=department_count,
            programme_count=programme_count,
        )

    async def attendance_summary(self, tenant_id: PydanticObjectId) -> AttendanceDashboardSummary:
        submitted = await AttendanceSession.find(
            Eq(AttendanceSession.tenant_id, tenant_id),
            Eq(AttendanceSession.status, AttendanceSessionStatus.SUBMITTED),
        ).count()
        pending = await PendingAttendanceSubmission.find(Eq(PendingAttendanceSubmission.tenant_id, tenant_id)).count()
        corrections = await AttendanceCorrectionRequest.find(
            Eq(AttendanceCorrectionRequest.tenant_id, tenant_id),
            Eq(AttendanceCorrectionRequest.status, AttendanceCorrectionStatus.PENDING),
        ).count()
        return AttendanceDashboardSummary(
            sessions_submitted=submitted,
            pending_submissions=pending,
            correction_requests_open=corrections,
        )

    async def examination_summary(
        self,
        tenant_id: PydanticObjectId,
        *,
        academic_year_label: str | None,
        semester_label: str | None,
    ) -> ExaminationDashboardSummary:
        exam_query: dict[str, Any] = {"tenant_id": tenant_id}
        if academic_year_label:
            exam_query["academic_year_label"] = academic_year_label
        if semester_label:
            exam_query["semester_label"] = semester_label
        scheduled = await ExaminationSchedule.find(exam_query).count()
        pending_eval = await PendingAssignmentEvaluation.find(Eq(PendingAssignmentEvaluation.tenant_id, tenant_id)).count()
        pub_filters: dict[str, Any] = {
            "tenant_id": tenant_id,
            "status": SemesterResultPublicationStatus.PUBLISHED,
        }
        if academic_year_label:
            pub_filters["academic_year_label"] = academic_year_label
        if semester_label:
            pub_filters["semester_label"] = semester_label
        published = await SemesterResultPublication.find(pub_filters).count()
        return ExaminationDashboardSummary(
            scheduled_exams=scheduled,
            pending_evaluations=pending_eval,
            published_results=published,
        )

    async def finance_summary(self, tenant_id: PydanticObjectId) -> FinanceDashboardSummary:
        collected = 0.0
        txs = await PaymentTransaction.find(
            Eq(PaymentTransaction.tenant_id, tenant_id),
            Eq(PaymentTransaction.status, PaymentTransactionStatus.SUCCESS),
        ).to_list()
        collected = sum(t.amount for t in txs)

        open_demands = await StudentFeeDemand.find(
            Eq(StudentFeeDemand.tenant_id, tenant_id),
            In(StudentFeeDemand.status, [FeeDemandStatus.OPEN, FeeDemandStatus.PARTIALLY_PAID, FeeDemandStatus.OVERDUE]),
        ).to_list()
        outstanding = sum(max(d.amount, 0) for d in open_demands)
        overdue = sum(1 for d in open_demands if d.status == FeeDemandStatus.OVERDUE)
        return FinanceDashboardSummary(
            collected_amount=round(collected, 2),
            outstanding_amount=round(outstanding, 2),
            open_demands=len(open_demands),
            overdue_demands=overdue,
        )

    async def library_hostel_summary(self, tenant_id: PydanticObjectId) -> LibraryHostelSummary:
        catalog = await LibraryCatalogItem.find(Eq(LibraryCatalogItem.tenant_id, tenant_id)).count()
        circulation = await LibraryCirculation.find(
            Eq(LibraryCirculation.tenant_id, tenant_id),
            Eq(LibraryCirculation.status, LibraryCirculationStatus.ACTIVE),
        ).count()
        fines = await LibraryFine.find(
            Eq(LibraryFine.tenant_id, tenant_id),
            Eq(LibraryFine.status, LibraryFineStatus.OPEN),
        ).count()
        allocations = await HostelRoomAllocation.find(Eq(HostelRoomAllocation.tenant_id, tenant_id)).count()
        hostel_pending = await HostelApplication.find(
            Eq(HostelApplication.tenant_id, tenant_id),
            Eq(HostelApplication.status, HostelApplicationStatus.SUBMITTED),
        ).count()
        return LibraryHostelSummary(
            catalog_items=catalog,
            active_circulation=circulation,
            open_fines=fines,
            hostel_allocations=allocations,
            pending_hostel_applications=hostel_pending,
        )

    async def integration_health(self, tenant_id: PydanticObjectId) -> list[IntegrationHealthSummary]:
        configs = await IntegrationConfiguration.find(
            Eq(IntegrationConfiguration.scope, IntegrationScope.TENANT),
            Eq(IntegrationConfiguration.tenant_id, tenant_id),
        ).to_list()
        results: list[IntegrationHealthSummary] = []
        for cfg in configs:
            health = await IntegrationHealth.find_one(Eq(IntegrationHealth.configuration_id, cfg.id))
            results.append(
                IntegrationHealthSummary(
                    provider_code=cfg.provider_code,
                    status=health.status.value if health else "unknown",
                    last_check_at=health.last_check_at if health else None,
                    detail=health.detail if health else None,
                )
            )
        return results

    async def upcoming_events(
        self,
        tenant_id: PydanticObjectId,
        *,
        from_time: datetime,
        to_time: datetime,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        rows = await (
            AcademicCalendarEvent.find(
                {
                    "tenant_id": tenant_id,
                    "event_at": {"$gte": from_time, "$lte": to_time},
                }
            )
            .sort("+event_at")
            .limit(limit)
            .to_list()
        )
        return [
            {
                "title": row.title,
                "event_type": row.event_type,
                "event_at": row.event_at.isoformat(),
            }
            for row in rows
        ]

    async def institutional_notifications(self, tenant_id: PydanticObjectId, *, limit: int = 10) -> list[NotificationSummary]:
        from app.modules.faculty.communication_models import FacultyAnnouncement

        announcements = await (
            FacultyAnnouncement.find(Eq(FacultyAnnouncement.tenant_id, tenant_id))
            .sort("-created_at")
            .limit(limit)
            .to_list()
        )
        return [
            NotificationSummary(
                title=row.title,
                message=row.body[:500],
                severity="info",
                created_at=row.created_at,
            )
            for row in announcements
        ]

    async def pending_approvals(
        self,
        tenant_id: PydanticObjectId,
        *,
        department_id: PydanticObjectId | None = None,
        limit: int = 50,
    ) -> list[PendingApprovalItem]:
        items: list[PendingApprovalItem] = []

        for row in await PendingAttendanceSubmission.find(Eq(PendingAttendanceSubmission.tenant_id, tenant_id)).limit(limit).to_list():
            items.append(
                PendingApprovalItem(
                    category=PendingApprovalCategory.ATTENDANCE,
                    title=f"Attendance pending — {row.class_label} {row.section}",
                    submitted_at=row.created_at,
                    reference_id=str(row.id),
                )
            )

        for row in await PendingAssignmentEvaluation.find(Eq(PendingAssignmentEvaluation.tenant_id, tenant_id)).limit(limit).to_list():
            items.append(
                PendingApprovalItem(
                    category=PendingApprovalCategory.ASSESSMENT,
                    title=f"Marks evaluation — {row.course_code}",
                    submitted_at=row.due_at if row.due_at else datetime.now(timezone.utc),
                    reference_id=str(row.id),
                )
            )

        for row in await LeaveRequest.find(
            Eq(LeaveRequest.tenant_id, tenant_id),
            Eq(LeaveRequest.status, LeaveRequestStatus.SUBMITTED),
        ).limit(limit).to_list():
            items.append(
                PendingApprovalItem(
                    category=PendingApprovalCategory.LEAVE,
                    title=f"Leave request — {row.leave_type}",
                    submitted_at=row.created_at,
                    reference_id=str(row.id),
                )
            )

        for row in await StudentAcademicRequest.find(
            Eq(StudentAcademicRequest.tenant_id, tenant_id),
            In(
                StudentAcademicRequest.status,
                [StudentAcademicRequestStatus.SUBMITTED, StudentAcademicRequestStatus.UNDER_REVIEW],
            ),
        ).limit(limit).to_list():
            items.append(
                PendingApprovalItem(
                    category=PendingApprovalCategory.ENROLLMENT,
                    title=f"Academic request — {row.request_type.value}",
                    submitted_at=row.submitted_at or row.created_at,
                    reference_id=str(row.id),
                )
            )

        for row in await StudentProfileCorrectionRequest.find(
            Eq(StudentProfileCorrectionRequest.tenant_id, tenant_id),
            Eq(StudentProfileCorrectionRequest.status, StudentDocumentRequestStatus.SUBMITTED),
        ).limit(limit).to_list():
            items.append(
                PendingApprovalItem(
                    category=PendingApprovalCategory.PROFILE_CORRECTION,
                    title="Profile correction request",
                    submitted_at=row.created_at,
                    reference_id=str(row.id),
                )
            )

        for row in await HostelApplication.find(
            Eq(HostelApplication.tenant_id, tenant_id),
            Eq(HostelApplication.status, HostelApplicationStatus.SUBMITTED),
        ).limit(limit).to_list():
            items.append(
                PendingApprovalItem(
                    category=PendingApprovalCategory.HOSTEL,
                    title="Hostel application",
                    submitted_at=row.submitted_at,
                    reference_id=str(row.id),
                )
            )

        for row in await StudentServiceRequest.find(
            Eq(StudentServiceRequest.tenant_id, tenant_id),
            In(
                StudentServiceRequest.status,
                [StudentServiceRequestStatus.SUBMITTED, StudentServiceRequestStatus.UNDER_REVIEW],
            ),
        ).limit(limit).to_list():
            items.append(
                PendingApprovalItem(
                    category=PendingApprovalCategory.STUDENT_REQUEST,
                    title=row.title,
                    submitted_at=row.created_at,
                    reference_id=row.request_id,
                )
            )

        items.sort(key=lambda i: i.submitted_at, reverse=True)
        return items[:limit]

    async def unresolved_support_requests(self, tenant_id: PydanticObjectId, *, limit: int = 20) -> list[SupportRequestSummary]:
        rows = await (
            StudentServiceRequest.find(
                Eq(StudentServiceRequest.tenant_id, tenant_id),
                In(
                    StudentServiceRequest.status,
                    [StudentServiceRequestStatus.SUBMITTED, StudentServiceRequestStatus.UNDER_REVIEW],
                ),
            )
            .sort("-created_at")
            .limit(limit)
            .to_list()
        )
        return [
            SupportRequestSummary(
                request_id=row.request_id,
                title=row.title,
                status=row.status.value if hasattr(row.status, "value") else str(row.status),
                category=row.category.value if hasattr(row.category, "value") else str(row.category),
                created_at=row.created_at,
            )
            for row in rows
        ]

    async def recent_student_activities(
        self,
        tenant_id: PydanticObjectId,
        *,
        from_time: datetime,
        limit: int = 15,
    ) -> list[ActivitySummary]:
        rows = await (
            StudentActivityLog.find(
                Eq(StudentActivityLog.tenant_id, tenant_id),
                {"created_at": {"$gte": from_time}},
            )
            .sort("-created_at")
            .limit(limit)
            .to_list()
        )
        return [
            ActivitySummary(
                activity_id=str(row.id),
                category="student",
                title=row.title,
                occurred_at=row.created_at,
                reference_id=str(row.user_id),
            )
            for row in rows
        ]

    async def recent_faculty_activities(
        self,
        tenant_id: PydanticObjectId,
        *,
        from_time: datetime,
        limit: int = 15,
    ) -> list[ActivitySummary]:
        rows = await (
            FacultyActivityLog.find(Eq(FacultyActivityLog.tenant_id, tenant_id))
            .find({"occurred_at": {"$gte": from_time}})
            .sort("-occurred_at")
            .limit(limit)
            .to_list()
        )
        return [
            ActivitySummary(
                activity_id=str(row.id),
                category="faculty",
                title=row.title,
                occurred_at=row.occurred_at,
                reference_id=str(row.user_id),
            )
            for row in rows
        ]

    async def recent_admissions(
        self,
        tenant_id: PydanticObjectId,
        *,
        from_time: datetime,
        limit: int = 10,
    ) -> list[ActivitySummary]:
        profiles = await (
            StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id))
            .find({"created_at": {"$gte": from_time}})
            .sort("-created_at")
            .limit(limit)
            .to_list()
        )
        results: list[ActivitySummary] = []
        for profile in profiles:
            user = await User.get(profile.user_id)
            results.append(
                ActivitySummary(
                    activity_id=str(profile.id),
                    category="admission",
                    title=f"New student — {user.full_name if user else profile.roll_number or 'unknown'}",
                    occurred_at=profile.created_at,
                    reference_id=str(profile.user_id),
                )
            )
        return results
