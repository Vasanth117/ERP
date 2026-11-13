"""Faculty assessment assignment validation."""

from beanie import PydanticObjectId

from app.core.exceptions import AppError
from app.modules.examinations.models import Assessment, AssessmentComponent, FacultyAssessmentAssignment


async def require_assessment_assignment(
    tenant_id: PydanticObjectId,
    faculty_user_id: PydanticObjectId,
    assessment_id: str,
    *,
    course_code: str | None = None,
    section: str | None = None,
) -> FacultyAssessmentAssignment:
    filters: dict = {
        "tenant_id": tenant_id,
        "faculty_user_id": faculty_user_id,
        "assessment_id": assessment_id,
    }
    if course_code:
        filters["course_code"] = course_code
    if section:
        filters["section"] = section
    row = await FacultyAssessmentAssignment.find_one(filters)
    if row is None:
        raise AppError(
            code="FORBIDDEN",
            message="You are not assigned to this assessment",
            status_code=403,
        )
    return row


async def get_component_or_404(
    tenant_id: PydanticObjectId, assessment_id: str, component_id: str
) -> AssessmentComponent:
    component = await AssessmentComponent.find_one(
        {"tenant_id": tenant_id, "assessment_id": assessment_id, "component_id": component_id}
    )
    if component is None:
        raise AppError(code="NOT_FOUND", message="Assessment component not found", status_code=404)
    return component


async def assert_faculty_may_enter(component: AssessmentComponent) -> None:
    if component.is_official_final or not component.faculty_may_enter:
        raise AppError(
            code="FORBIDDEN",
            message="Official final results cannot be entered or modified by faculty",
            status_code=403,
        )


async def assert_assessment_not_published(tenant_id: PydanticObjectId, assessment_id: str) -> Assessment:
    assessment = await Assessment.find_one({"tenant_id": tenant_id, "assessment_id": assessment_id})
    if assessment is None:
        raise AppError(code="NOT_FOUND", message="Assessment not found", status_code=404)
    if assessment.final_results_published or assessment.locked:
        raise AppError(
            code="FORBIDDEN",
            message="Official final results are published and cannot be changed",
            status_code=403,
        )
    return assessment
