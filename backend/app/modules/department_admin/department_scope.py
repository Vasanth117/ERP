"""Department boundary helpers for faculty and academic scope."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.common.roles import Role
from app.core.exceptions import AppError
from app.modules.academics.curriculum_models import CourseRecord
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import FacultyEmploymentStatus, FacultyRecord
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.modules.faculty.models import FacultyAssignment, FacultyProfile


async def department_programme_codes(institution: InstitutionDepartment) -> list[str]:
    return [c.upper() for c in institution.programme_codes]


async def department_course_codes(tenant_id: PydanticObjectId, central_department_id: PydanticObjectId) -> set[str]:
    courses = await CourseRecord.find(
        Eq(CourseRecord.tenant_id, tenant_id),
        Eq(CourseRecord.department_id, central_department_id),
        Eq(CourseRecord.is_active, True),
    ).to_list()
    return {c.course_code.upper() for c in courses}


async def faculty_user_ids_in_department(
    tenant_id: PydanticObjectId,
    central_department_id: PydanticObjectId,
    *,
    include_cross_teaching: bool = True,
) -> set[PydanticObjectId]:
    ids: set[PydanticObjectId] = set()
    for profile in await FacultyProfile.find(
        Eq(FacultyProfile.tenant_id, tenant_id),
        Eq(FacultyProfile.department_id, central_department_id),
    ).to_list():
        ids.add(profile.user_id)
    for user in await User.find(
        Eq(User.tenant_id, tenant_id),
        Eq(User.role, Role.FACULTY),
        Eq(User.department_id, central_department_id),
    ).to_list():
        ids.add(user.id)
    if include_cross_teaching:
        course_codes = list(await department_course_codes(tenant_id, central_department_id))
        if course_codes:
            for row in await FacultyAssignment.find(
                Eq(FacultyAssignment.tenant_id, tenant_id),
                In(FacultyAssignment.course_code, course_codes),
            ).to_list():
                ids.add(row.user_id)
    return ids


async def assert_faculty_visible_to_department(
    tenant_id: PydanticObjectId,
    central_department_id: PydanticObjectId,
    faculty_user_id: PydanticObjectId,
) -> FacultyProfile:
    allowed = await faculty_user_ids_in_department(tenant_id, central_department_id)
    if faculty_user_id not in allowed:
        raise AppError(code="FORBIDDEN", message="Faculty is outside your department scope", status_code=403)
    profile = await FacultyProfile.find_one(
        Eq(FacultyProfile.tenant_id, tenant_id),
        Eq(FacultyProfile.user_id, faculty_user_id),
    )
    if profile is None:
        user = await User.get(faculty_user_id)
        if user is None or user.tenant_id != tenant_id:
            raise AppError(code="NOT_FOUND", message="Faculty not found", status_code=404)
        profile = FacultyProfile(tenant_id=tenant_id, user_id=faculty_user_id, department_id=user.department_id)
    record = await FacultyRecord.find_one(
        Eq(FacultyRecord.tenant_id, tenant_id),
        Eq(FacultyRecord.user_id, faculty_user_id),
    )
    if record and record.employment_status not in {
        FacultyEmploymentStatus.ACTIVE,
        FacultyEmploymentStatus.ON_LEAVE,
    }:
        raise AppError(code="FORBIDDEN", message="Faculty employment is not active", status_code=403)
    return profile


async def assert_course_in_department(
    tenant_id: PydanticObjectId,
    central_department_id: PydanticObjectId,
    course_code: str,
) -> CourseRecord:
    code = course_code.upper()
    course = await CourseRecord.find_one(
        Eq(CourseRecord.tenant_id, tenant_id),
        Eq(CourseRecord.course_code, code),
    )
    if course is None:
        raise AppError(code="NOT_FOUND", message="Course not found", status_code=404)
    allowed = await department_course_codes(tenant_id, central_department_id)
    in_scope = code in allowed or course.department_id == central_department_id
    if not in_scope:
        raise AppError(code="FORBIDDEN", message="Course is outside your department", status_code=403)
    return course