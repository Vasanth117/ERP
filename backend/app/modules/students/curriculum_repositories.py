"""Registration and curriculum reference repositories."""

from beanie import PydanticObjectId

from app.modules.students.curriculum_models import (
    CourseCatalogReference,
    CoursePrerequisite,
    CourseRegistrationRequest,
    ElectiveGroup,
    ElectiveOption,
    RegistrationHistoryEntry,
    RegistrationPolicyReference,
    StudentCourseRegistration,
    StudentElectiveSelection,
)
from app.modules.students.registration_enums import CourseRegistrationStatus, RegistrationRequestStatus
from app.repositories.base import TenantScopedRepository


class CourseCatalogRepository(TenantScopedRepository[CourseCatalogReference]):
    def __init__(self) -> None:
        super().__init__(CourseCatalogReference)

    async def list_for_term(
        self,
        tenant_id: PydanticObjectId,
        programme_code: str,
        academic_year_label: str,
        semester_label: str,
        *,
        open_only: bool = False,
    ) -> list[CourseCatalogReference]:
        filters = {
            "tenant_id": tenant_id,
            "programme_code": programme_code,
            "academic_year_label": academic_year_label,
            "semester_label": semester_label,
        }
        if open_only:
            filters["is_open_for_registration"] = True
        return await CourseCatalogReference.find(filters).sort("course_code").to_list()


class RegistrationPolicyRepository(TenantScopedRepository[RegistrationPolicyReference]):
    def __init__(self) -> None:
        super().__init__(RegistrationPolicyReference)

    async def get_policy(
        self,
        tenant_id: PydanticObjectId,
        programme_code: str,
        academic_year_label: str,
        semester_label: str,
    ) -> RegistrationPolicyReference | None:
        return await RegistrationPolicyReference.find_one(
            {
                "tenant_id": tenant_id,
                "programme_code": programme_code,
                "academic_year_label": academic_year_label,
                "semester_label": semester_label,
            }
        )


class StudentRegistrationRepository(TenantScopedRepository[StudentCourseRegistration]):
    def __init__(self) -> None:
        super().__init__(StudentCourseRegistration)

    async def list_for_student_term(
        self,
        tenant_id: PydanticObjectId,
        user_id: PydanticObjectId,
        academic_year_label: str,
        semester_label: str,
    ) -> list[StudentCourseRegistration]:
        return await StudentCourseRegistration.find(
            {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "academic_year_label": academic_year_label,
                "semester_label": semester_label,
            }
        ).sort("course_code").to_list()

    async def completed_course_ids(
        self, tenant_id: PydanticObjectId, user_id: PydanticObjectId
    ) -> set[str]:
        rows = await StudentCourseRegistration.find(
            {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "status": CourseRegistrationStatus.APPROVED,
            }
        ).to_list()
        return {r.course_id for r in rows}


class RegistrationRequestRepository(TenantScopedRepository[CourseRegistrationRequest]):
    def __init__(self) -> None:
        super().__init__(CourseRegistrationRequest)

    async def active_draft(
        self,
        tenant_id: PydanticObjectId,
        user_id: PydanticObjectId,
        academic_year_label: str,
        semester_label: str,
    ) -> CourseRegistrationRequest | None:
        return await CourseRegistrationRequest.find_one(
            {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "academic_year_label": academic_year_label,
                "semester_label": semester_label,
                "status": {"$in": [RegistrationRequestStatus.DRAFT, RegistrationRequestStatus.SUBMITTED]},
            }
        )


class RegistrationHistoryRepository(TenantScopedRepository[RegistrationHistoryEntry]):
    def __init__(self) -> None:
        super().__init__(RegistrationHistoryEntry)
