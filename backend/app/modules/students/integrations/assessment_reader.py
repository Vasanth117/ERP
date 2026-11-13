"""Read assessments and marks for enrolled students."""

from beanie import PydanticObjectId

from app.modules.academics.models import ExaminationSchedule, UpcomingAssessment
from app.modules.examinations.enums import StudentMarkStatus
from app.modules.examinations.models import (
    Assessment,
    AssessmentComponent,
    MarksSubmissionBatch,
    StudentAssessmentMark,
)
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.assessment_enums import CIA_COMPONENT_TYPES

_reader = StudentDataReader()
_PUBLISHED_STATUSES = frozenset({StudentMarkStatus.APPROVED, StudentMarkStatus.LOCKED})


async def student_course_codes(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
) -> set[str]:
    roster = await _reader.roster_entries(tenant_id, user_id, academic_year_label=year, semester_label=semester)
    return {r.course_code for r in roster}


async def cia_schedules(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
) -> list[UpcomingAssessment]:
    codes = await student_course_codes(tenant_id, user_id, year=year, semester=semester)
    if not codes:
        return []
    return (
        await UpcomingAssessment.find(
            {
                "tenant_id": tenant_id,
                "academic_year_label": year,
                "semester_label": semester,
                "course_code": {"$in": list(codes)},
            }
        )
        .sort("scheduled_at")
        .to_list()
    )


async def cia_examination_slots(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
) -> list[ExaminationSchedule]:
    codes = await student_course_codes(tenant_id, user_id, year=year, semester=semester)
    if not codes:
        return []
    rows = await ExaminationSchedule.find(
        {
            "tenant_id": tenant_id,
            "academic_year_label": year,
            "semester_label": semester,
            "course_code": {"$in": list(codes)},
            "exam_type": {"$in": ["cia", "internal", "CIA", "internal_assessment"]},
        }
    ).sort("scheduled_at").to_list()
    return rows


async def assessments_for_student(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
) -> list[Assessment]:
    codes = await student_course_codes(tenant_id, user_id, year=year, semester=semester)
    if not codes:
        return []
    return await Assessment.find(
        {
            "tenant_id": tenant_id,
            "academic_year_label": year,
            "semester_label": semester,
            "course_code": {"$in": list(codes)},
        }
    ).to_list()


async def cia_components(tenant_id: PydanticObjectId, assessment_id: str) -> list[AssessmentComponent]:
    components = await AssessmentComponent.find({"tenant_id": tenant_id, "assessment_id": assessment_id}).to_list()
    return [c for c in components if c.component_type.value in CIA_COMPONENT_TYPES]


async def published_mark(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    assessment_id: str,
    component_id: str,
) -> StudentAssessmentMark | None:
    mark = await StudentAssessmentMark.find_one(
        {
            "tenant_id": tenant_id,
            "student_user_id": user_id,
            "assessment_id": assessment_id,
            "component_id": component_id,
            "status": {"$in": list(_PUBLISHED_STATUSES)},
        }
    )
    return mark


async def all_marks_for_student(
    tenant_id: PydanticObjectId, user_id: PydanticObjectId, *, published_only: bool = True
) -> list[StudentAssessmentMark]:
    filters: dict = {"tenant_id": tenant_id, "student_user_id": user_id}
    if published_only:
        filters["status"] = {"$in": list(_PUBLISHED_STATUSES)}
    return await StudentAssessmentMark.find(filters).sort("-updated_at").to_list()


async def batch_published(component_id: str, course_code: str, section: str) -> MarksSubmissionBatch | None:
    return await MarksSubmissionBatch.find_one(
        {
            "component_id": component_id,
            "course_code": course_code,
            "status": "approved",
        }
    )
