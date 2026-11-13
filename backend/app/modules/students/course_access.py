"""Verify a student may access a course's academic content."""

from beanie import PydanticObjectId

from app.core.exceptions import AppError
from app.modules.academics.curriculum_models import CourseRecord, EnrollmentRosterEntry
from app.modules.students.models import StudentEnrollment
from app.modules.students.curriculum_models import StudentCourseRegistration
from app.modules.students.registration_enums import CourseRegistrationStatus


async def resolve_course_id(tenant_id: PydanticObjectId, course_code: str) -> str:
    course = await CourseRecord.find_one({"tenant_id": tenant_id, "course_code": course_code})
    if course is None:
        raise AppError(code="NOT_FOUND", message="Course not found", status_code=404)
    return course.course_id


async def assert_student_course_access(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    course_code: str,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
) -> None:
    """Student must be on roster, in official enrollment, or have non-cancelled registration."""
    course = await CourseRecord.find_one({"tenant_id": tenant_id, "course_code": course_code})
    if course is None:
        raise AppError(code="NOT_FOUND", message="Course not found", status_code=404)
    roster_filters: dict = {
        "tenant_id": tenant_id,
        "student_user_id": user_id,
        "course_code": course_code,
    }
    if academic_year_label:
        roster_filters["academic_year_label"] = academic_year_label
    if semester_label:
        roster_filters["semester_label"] = semester_label
    if await EnrollmentRosterEntry.find_one(roster_filters):
        return
    enroll_filters: dict = {"tenant_id": tenant_id, "user_id": user_id, "course_code": course_code}
    if academic_year_label:
        enroll_filters["academic_year_label"] = academic_year_label
    if semester_label:
        enroll_filters["semester_label"] = semester_label
    if await StudentEnrollment.find_one(enroll_filters):
        return
    reg_filters: dict = {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "course_id": course.course_id,
        "status": {"$nin": [CourseRegistrationStatus.CANCELLED, CourseRegistrationStatus.REJECTED]},
    }
    if academic_year_label:
        reg_filters["academic_year_label"] = academic_year_label
    if semester_label:
        reg_filters["semester_label"] = semester_label
    if await StudentCourseRegistration.find_one(reg_filters):
        return
    raise AppError(code="FORBIDDEN", message="You are not authorized to view this course", status_code=403)
