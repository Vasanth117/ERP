"""Academic data access (tenant-scoped reads)."""

from beanie import PydanticObjectId

from app.modules.academics.curriculum_models import (
    CourseLearningOutcome,
    CourseRecord,
    CourseSubjectMapping,
    CurriculumRecord,
    EnrollmentRosterEntry,
    SectionOffering,
    SubjectRecord,
    SyllabusRecord,
)
from app.modules.academics.models import (
    AcademicYearContext,
    ClassSession,
    ExaminationSchedule,
    TimetableChangeLog,
    TimetableEntry,
)
from app.repositories.base import TenantScopedRepository


class CourseRepository(TenantScopedRepository[CourseRecord]):
    def __init__(self) -> None:
        super().__init__(CourseRecord)

    async def get_by_code(self, tenant_id: PydanticObjectId, course_code: str) -> CourseRecord | None:
        return await CourseRecord.find_one({"tenant_id": tenant_id, "course_code": course_code})


class SubjectRepository(TenantScopedRepository[SubjectRecord]):
    def __init__(self) -> None:
        super().__init__(SubjectRecord)


class AcademicQueryRepository:
    async def current_term(self, tenant_id: PydanticObjectId) -> AcademicYearContext | None:
        return await AcademicYearContext.find_one({"tenant_id": tenant_id, "is_current": True})

    async def subject_mappings(self, tenant_id: PydanticObjectId, course_id: str) -> list[CourseSubjectMapping]:
        return await CourseSubjectMapping.find({"tenant_id": tenant_id, "course_id": course_id}).sort(
            "sequence_order"
        ).to_list()

    async def syllabus(
        self,
        tenant_id: PydanticObjectId,
        course_id: str,
        *,
        subject_id: str | None = None,
        year: str | None = None,
        semester: str | None = None,
    ) -> SyllabusRecord | None:
        filters: dict = {"tenant_id": tenant_id, "course_id": course_id, "approved": True}
        if subject_id:
            filters["subject_id"] = subject_id
        if year:
            filters["academic_year_label"] = year
        if semester:
            filters["semester_label"] = semester
        return await SyllabusRecord.find_one(filters)

    async def curriculum(
        self, tenant_id: PydanticObjectId, course_id: str, year: str, semester: str
    ) -> CurriculumRecord | None:
        return await CurriculumRecord.find_one(
            {
                "tenant_id": tenant_id,
                "course_id": course_id,
                "academic_year_label": year,
                "semester_label": semester,
                "approved": True,
            }
        )

    async def learning_outcomes(
        self, tenant_id: PydanticObjectId, course_id: str, year: str, semester: str
    ) -> CourseLearningOutcome | None:
        return await CourseLearningOutcome.find_one(
            {
                "tenant_id": tenant_id,
                "course_id": course_id,
                "academic_year_label": year,
                "semester_label": semester,
            }
        )

    async def roster(
        self,
        tenant_id: PydanticObjectId,
        course_id: str,
        section_code: str,
        *,
        subject_id: str | None = None,
    ) -> list[EnrollmentRosterEntry]:
        filters: dict = {
            "tenant_id": tenant_id,
            "course_id": course_id,
            "section_code": section_code,
        }
        if subject_id:
            filters["subject_id"] = subject_id
        return await EnrollmentRosterEntry.find(filters).sort("roll_number").to_list()

    async def sections_for_course(self, tenant_id: PydanticObjectId, course_id: str) -> list[SectionOffering]:
        return await SectionOffering.find({"tenant_id": tenant_id, "course_id": course_id}).to_list()

    async def timetable(
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

    async def class_sessions(
        self,
        tenant_id: PydanticObjectId,
        faculty_user_id: PydanticObjectId,
        *,
        from_time=None,
        to_time=None,
    ) -> list[ClassSession]:
        filters: dict = {"tenant_id": tenant_id, "faculty_user_id": faculty_user_id}
        if from_time is not None or to_time is not None:
            range_filter: dict = {}
            if from_time is not None:
                range_filter["$gte"] = from_time
            if to_time is not None:
                range_filter["$lte"] = to_time
            filters["scheduled_start"] = range_filter
        return await ClassSession.find(filters).sort("scheduled_start").to_list()

    async def examinations(
        self, tenant_id: PydanticObjectId, faculty_user_id: PydanticObjectId
    ) -> list[ExaminationSchedule]:
        return await ExaminationSchedule.find(
            {"tenant_id": tenant_id, "faculty_user_id": faculty_user_id}
        ).sort("scheduled_at").to_list()

    async def timetable_changes(
        self, tenant_id: PydanticObjectId, faculty_user_id: PydanticObjectId, *, limit: int = 50
    ) -> list[TimetableChangeLog]:
        return (
            await TimetableChangeLog.find({"tenant_id": tenant_id, "faculty_user_id": faculty_user_id})
            .sort("-effective_at")
            .limit(limit)
            .to_list()
        )
