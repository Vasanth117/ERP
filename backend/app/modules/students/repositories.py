"""Tenant-scoped student portal data access."""

from beanie import PydanticObjectId

from app.modules.students.enums import StudentActivityType, StudentEnrollmentStatus
from app.modules.students.models import (
    StudentAcademicRecord,
    StudentAcademicRequest,
    StudentActivityLog,
    StudentDashboardPreferences,
    StudentEnrollment,
    StudentEnrollmentHistory,
    StudentProfile,
)
from app.repositories.base import TenantScopedRepository


class StudentProfileRepository(TenantScopedRepository[StudentProfile]):
    def __init__(self) -> None:
        super().__init__(StudentProfile)

    async def get_by_user(self, tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> StudentProfile | None:
        return await StudentProfile.find_one({"tenant_id": tenant_id, "user_id": user_id})


class StudentAcademicRecordRepository(TenantScopedRepository[StudentAcademicRecord]):
    def __init__(self) -> None:
        super().__init__(StudentAcademicRecord)

    async def get_current(
        self,
        tenant_id: PydanticObjectId,
        user_id: PydanticObjectId,
        *,
        academic_year_label: str,
        semester_label: str,
    ) -> StudentAcademicRecord | None:
        return await StudentAcademicRecord.find_one(
            {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "academic_year_label": academic_year_label,
                "semester_label": semester_label,
            }
        )


class StudentEnrollmentRepository(TenantScopedRepository[StudentEnrollment]):
    def __init__(self) -> None:
        super().__init__(StudentEnrollment)

    async def list_for_term(
        self,
        tenant_id: PydanticObjectId,
        user_id: PydanticObjectId,
        *,
        academic_year_label: str,
        semester_label: str,
        status: StudentEnrollmentStatus | None = StudentEnrollmentStatus.ACTIVE,
    ) -> list[StudentEnrollment]:
        filters = {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "academic_year_label": academic_year_label,
            "semester_label": semester_label,
        }
        if status is not None:
            filters["status"] = status
        return await StudentEnrollment.find(filters).sort("course_code").to_list()


class StudentEnrollmentHistoryRepository(TenantScopedRepository[StudentEnrollmentHistory]):
    def __init__(self) -> None:
        super().__init__(StudentEnrollmentHistory)

    async def list_for_user(
        self,
        tenant_id: PydanticObjectId,
        user_id: PydanticObjectId,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[StudentEnrollmentHistory], int]:
        query = StudentEnrollmentHistory.find({"tenant_id": tenant_id, "user_id": user_id}).sort("-closed_at")
        total = await query.count()
        items = await query.skip(skip).limit(limit).to_list()
        return items, total


class StudentAcademicRequestRepository(TenantScopedRepository[StudentAcademicRequest]):
    def __init__(self) -> None:
        super().__init__(StudentAcademicRequest)

    async def list_open(
        self, tenant_id: PydanticObjectId, user_id: PydanticObjectId, *, limit: int = 20
    ) -> list[StudentAcademicRequest]:
        return (
            await StudentAcademicRequest.find(
                {
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "status": {"$in": ["submitted", "under_review"]},
                }
            )
            .sort("-submitted_at")
            .limit(limit)
            .to_list()
        )


class StudentActivityRepository(TenantScopedRepository[StudentActivityLog]):
    def __init__(self) -> None:
        super().__init__(StudentActivityLog)

    async def append(
        self,
        *,
        tenant_id: PydanticObjectId,
        user_id: PydanticObjectId,
        activity_type: StudentActivityType,
        title: str,
        description: str | None = None,
        metadata: dict | None = None,
    ) -> StudentActivityLog:
        row = StudentActivityLog(
            tenant_id=tenant_id,
            user_id=user_id,
            activity_type=activity_type,
            title=title,
            description=description,
            metadata=metadata or {},
        )
        await row.insert()
        return row

    async def page_for_user(
        self,
        tenant_id: PydanticObjectId,
        user_id: PydanticObjectId,
        *,
        skip: int,
        limit: int,
    ) -> tuple[list[StudentActivityLog], int]:
        query = StudentActivityLog.find({"tenant_id": tenant_id, "user_id": user_id}).sort("-created_at")
        total = await query.count()
        items = await query.skip(skip).limit(limit).to_list()
        return items, total


class StudentDashboardPreferencesRepository(TenantScopedRepository[StudentDashboardPreferences]):
    def __init__(self) -> None:
        super().__init__(StudentDashboardPreferences)

    async def get_or_create(self, tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> StudentDashboardPreferences:
        existing = await StudentDashboardPreferences.find_one({"tenant_id": tenant_id, "user_id": user_id})
        if existing is not None:
            return existing
        prefs = StudentDashboardPreferences(tenant_id=tenant_id, user_id=user_id)
        await prefs.insert()
        return prefs
