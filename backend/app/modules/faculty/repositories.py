"""Tenant-scoped faculty data access."""

from datetime import datetime
from typing import Any

from beanie import PydanticObjectId

from app.common.time import utcnow

from app.modules.faculty.enums import AssignmentStatus, FacultyActivityType
from app.modules.faculty.models import (
    FacultyActivityLog,
    FacultyAssignment,
    FacultyDashboardPreferences,
    FacultyNotification,
    FacultyProfile,
    FacultyWorkload,
)
from app.repositories.base import TenantScopedRepository


class FacultyProfileRepository(TenantScopedRepository[FacultyProfile]):
    def __init__(self) -> None:
        super().__init__(FacultyProfile)

    async def get_by_user(self, tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> FacultyProfile | None:
        return await FacultyProfile.find_one({"tenant_id": tenant_id, "user_id": user_id})


class FacultyAssignmentRepository(TenantScopedRepository[FacultyAssignment]):
    def __init__(self) -> None:
        super().__init__(FacultyAssignment)

    async def list_active_for_user(
        self,
        tenant_id: PydanticObjectId,
        user_id: PydanticObjectId,
        *,
        academic_year_label: str | None = None,
        semester_label: str | None = None,
    ) -> list[FacultyAssignment]:
        filters: dict[str, Any] = {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "status": AssignmentStatus.ACTIVE,
        }
        if academic_year_label:
            filters["academic_year_label"] = academic_year_label
        if semester_label:
            filters["semester_label"] = semester_label
        return await FacultyAssignment.find(filters).sort("-updated_at").to_list()

    async def list_history_for_user(
        self,
        tenant_id: PydanticObjectId,
        user_id: PydanticObjectId,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[FacultyAssignment], int]:
        filters = {"tenant_id": tenant_id, "user_id": user_id}
        query = FacultyAssignment.find(filters).sort("-updated_at")
        total = await query.count()
        items = await query.skip(skip).limit(limit).to_list()
        return items, total


class FacultyWorkloadRepository(TenantScopedRepository[FacultyWorkload]):
    def __init__(self) -> None:
        super().__init__(FacultyWorkload)

    async def get_for_term(
        self,
        tenant_id: PydanticObjectId,
        user_id: PydanticObjectId,
        academic_year_label: str,
        semester_label: str,
    ) -> FacultyWorkload | None:
        return await FacultyWorkload.find_one(
            {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "academic_year_label": academic_year_label,
                "semester_label": semester_label,
            }
        )


class FacultyActivityRepository(TenantScopedRepository[FacultyActivityLog]):
    def __init__(self) -> None:
        super().__init__(FacultyActivityLog)

    async def list_for_user(
        self,
        tenant_id: PydanticObjectId,
        user_id: PydanticObjectId,
        *,
        skip: int,
        limit: int,
        activity_type: FacultyActivityType | None = None,
    ) -> tuple[list[FacultyActivityLog], int]:
        filters: dict[str, Any] = {"tenant_id": tenant_id, "user_id": user_id}
        if activity_type is not None:
            filters["activity_type"] = activity_type
        query = FacultyActivityLog.find(filters).sort("-occurred_at")
        total = await query.count()
        items = await query.skip(skip).limit(limit).to_list()
        return items, total

    async def append(
        self,
        *,
        tenant_id: PydanticObjectId,
        user_id: PydanticObjectId,
        activity_type: FacultyActivityType,
        title: str,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
        occurred_at: datetime | None = None,
        source_module: str = "faculty",
    ) -> FacultyActivityLog:
        entry = FacultyActivityLog(
            tenant_id=tenant_id,
            user_id=user_id,
            activity_type=activity_type,
            title=title,
            description=description,
            metadata=metadata or {},
            occurred_at=occurred_at or utcnow(),
            source_module=source_module,
        )
        await entry.insert()
        return entry


class FacultyNotificationRepository(TenantScopedRepository[FacultyNotification]):
    def __init__(self) -> None:
        super().__init__(FacultyNotification)

    async def list_for_user(
        self,
        tenant_id: PydanticObjectId,
        user_id: PydanticObjectId,
        *,
        limit: int = 20,
    ) -> list[FacultyNotification]:
        return (
            await FacultyNotification.find({"tenant_id": tenant_id, "user_id": user_id})
            .sort("-created_at")
            .limit(limit)
            .to_list()
        )


class FacultyDashboardPreferencesRepository(TenantScopedRepository[FacultyDashboardPreferences]):
    def __init__(self) -> None:
        super().__init__(FacultyDashboardPreferences)

    async def get_or_create(
        self, tenant_id: PydanticObjectId, user_id: PydanticObjectId
    ) -> FacultyDashboardPreferences:
        existing = await FacultyDashboardPreferences.find_one({"tenant_id": tenant_id, "user_id": user_id})
        if existing is not None:
            return existing
        prefs = FacultyDashboardPreferences(tenant_id=tenant_id, user_id=user_id)
        await prefs.insert()
        return prefs
