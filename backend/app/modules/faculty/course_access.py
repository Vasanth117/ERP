"""Validate faculty-course-section relationships."""

from beanie import PydanticObjectId

from app.core.exceptions import AppError
from app.modules.academics.curriculum_models import CourseRecord
from app.modules.faculty.enums import AssignmentStatus
from app.modules.faculty.models import FacultyAssignment


async def get_active_assignment(
    tenant_id: PydanticObjectId,
    faculty_user_id: PydanticObjectId,
    *,
    course_code: str | None = None,
    course_id: str | None = None,
    section: str | None = None,
) -> FacultyAssignment | None:
    filters: dict = {
        "tenant_id": tenant_id,
        "user_id": faculty_user_id,
        "status": AssignmentStatus.ACTIVE,
    }
    if course_code:
        filters["course_code"] = course_code
    if section:
        filters["section"] = section
    assignment = await FacultyAssignment.find_one(filters)
    if assignment is None:
        return None
    if course_id and assignment.course_id and assignment.course_id != course_id:
        return None
    return assignment


async def require_course_access(
    tenant_id: PydanticObjectId,
    faculty_user_id: PydanticObjectId,
    *,
    course_code: str,
    section: str | None = None,
) -> FacultyAssignment:
    assignment = await get_active_assignment(
        tenant_id,
        faculty_user_id,
        course_code=course_code,
        section=section,
    )
    if assignment is None:
        raise AppError(
            code="FORBIDDEN",
            message="You are not assigned to this course or section",
            status_code=403,
        )
    return assignment


async def resolve_course_id(tenant_id: PydanticObjectId, course_code: str) -> str:
    course = await CourseRecord.find_one({"tenant_id": tenant_id, "course_code": course_code})
    if course is None:
        raise AppError(code="NOT_FOUND", message="Course not found", status_code=404)
    return course.course_id
