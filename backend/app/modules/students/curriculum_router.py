"""Student curriculum and course registration routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.students.curriculum_service import (
    get_course_information,
    get_course_outcomes,
    get_curriculum,
    get_curriculum_overview,
    get_curriculum_semester_page,
    get_curriculum_subject_detail,
    get_curriculum_subject_list,
    get_curriculum_categories_electives_page,
    get_curriculum_history_page,
    get_curriculum_syllabus_page,
    get_prerequisites,
    get_syllabus,
    list_enrolled_courses,
    list_subjects_for_course,
    semester_subjects,
)
from app.modules.students.deps import enrollment_request_rate_limit, student_user
from app.modules.students.curriculum_schemas import (
    AvailableCourseRead,
    CourseInfoRead,
    CourseRegistrationRead,
    CurriculumOverviewRead,
    CurriculumSemesterPageRead,
    CurriculumSubjectDetailRead,
    CurriculumSubjectListRead,
    CurriculumCategoriesElectivesPageRead,
    CurriculumHistoryPageRead,
    CurriculumSyllabusPageRead,
    CurriculumRead,
    ElectiveGroupRead,
    ElectiveOptionRead,
    EnrolledCourseItemRead,
    LearningOutcomesDetailRead,
    PrerequisiteRead,
    RegistrationEligibilityRead,
    RegistrationHistoryRead,
    RegistrationCourseDetailPageRead,
    RegistrationCoursesPageRead,
    RegistrationElectivesPageRead,
    RegistrationOverviewPageRead,
    RegistrationReviewPageRead,
    RegistrationStatusPageRead,
    RegistrationRequestRead,
    RegistrationSelectionInput,
    RegistrationSubmitRead,
    RegistrationValidationRead,
    SemesterSubjectsRead,
    SubjectItemRead,
    SyllabusDetailRead,
)
from app.modules.students.registration_service import (
    cancel_registration,
    get_registration_course_detail_page,
    get_registration_courses_page,
    get_registration_electives_page,
    get_registration_eligibility,
    get_registration_overview_page,
    get_registration_review_page,
    get_registration_status_page,
    get_registration_request,
    list_available_courses,
    list_confirmed_registrations,
    list_elective_groups,
    list_elective_options,
    registration_history,
    save_registration_draft,
    submit_registration,
    update_registration,
    validate_course_selection,
)

curriculum_router = APIRouter()


@curriculum_router.get("/me/curriculum/courses", response_model=ApiResponse[list[EnrolledCourseItemRead]])
async def student_enrolled_courses_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[EnrolledCourseItemRead]]:
    data = await list_enrolled_courses(scope, user)
    return success_response(data, request_id=get_request_id())


@curriculum_router.get(
    "/me/curriculum/courses/{course_code}/subjects",
    response_model=ApiResponse[list[SubjectItemRead]],
)
async def student_course_subjects_route(
    course_code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[SubjectItemRead]]:
    data = await list_subjects_for_course(scope, user, course_code)
    return success_response(data, request_id=get_request_id())


@curriculum_router.get("/me/curriculum/overview", response_model=ApiResponse[CurriculumOverviewRead])
async def student_curriculum_overview_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[CurriculumOverviewRead]:
    data = await get_curriculum_overview(scope, user)
    return success_response(data, request_id=get_request_id())


@curriculum_router.get("/me/curriculum/subjects", response_model=ApiResponse[CurriculumSubjectListRead])
async def student_curriculum_subject_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    semester: int | None = None,
    category: str = "all",
    status: str = "all",
    q: str | None = None,
) -> ApiResponse[CurriculumSubjectListRead]:
    data = await get_curriculum_subject_list(
        scope,
        user,
        semester=semester,
        category=category,
        status=status,
        search_query=q,
    )
    return success_response(data, request_id=get_request_id())


@curriculum_router.get(
    "/me/curriculum/subjects/{course_code}",
    response_model=ApiResponse[CurriculumSubjectDetailRead],
)
async def student_curriculum_subject_detail_route(
    course_code: Annotated[str, Path(description="Course / subject code")],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[CurriculumSubjectDetailRead]:
    data = await get_curriculum_subject_detail(scope, user, course_code)
    return success_response(data, request_id=get_request_id())


@curriculum_router.get("/me/curriculum/semesters", response_model=ApiResponse[CurriculumSemesterPageRead])
async def student_curriculum_semester_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    semester: int | None = None,
) -> ApiResponse[CurriculumSemesterPageRead]:
    data = await get_curriculum_semester_page(scope, user, semester=semester)
    return success_response(data, request_id=get_request_id())


@curriculum_router.get("/me/curriculum/programme", response_model=ApiResponse[CurriculumRead])
async def student_curriculum_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[CurriculumRead]:
    data = await get_curriculum(scope, user)
    return success_response(data, request_id=get_request_id())


@curriculum_router.get("/me/curriculum/history", response_model=ApiResponse[CurriculumHistoryPageRead])
async def student_curriculum_history_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[CurriculumHistoryPageRead]:
    data = await get_curriculum_history_page(scope, user)
    return success_response(data, request_id=get_request_id())


@curriculum_router.get(
    "/me/curriculum/categories-electives",
    response_model=ApiResponse[CurriculumCategoriesElectivesPageRead],
)
async def student_curriculum_categories_electives_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[CurriculumCategoriesElectivesPageRead]:
    data = await get_curriculum_categories_electives_page(scope, user)
    return success_response(data, request_id=get_request_id())


@curriculum_router.get(
    "/me/curriculum/syllabus/{course_code}",
    response_model=ApiResponse[CurriculumSyllabusPageRead],
)
async def student_curriculum_syllabus_page_route(
    course_code: Annotated[str, Path(description="Course / subject code")],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    unit: int | None = None,
) -> ApiResponse[CurriculumSyllabusPageRead]:
    data = await get_curriculum_syllabus_page(scope, user, course_code, unit_no=unit)
    return success_response(data, request_id=get_request_id())


@curriculum_router.get(
    "/me/curriculum/courses/{course_code}/syllabus",
    response_model=ApiResponse[SyllabusDetailRead],
)
async def student_syllabus_route(
    course_code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    subject_id: str | None = None,
) -> ApiResponse[SyllabusDetailRead]:
    data = await get_syllabus(scope, user, course_code, subject_id=subject_id)
    return success_response(data, request_id=get_request_id())


@curriculum_router.get(
    "/me/curriculum/courses/{course_code}/outcomes",
    response_model=ApiResponse[LearningOutcomesDetailRead],
)
async def student_outcomes_route(
    course_code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[LearningOutcomesDetailRead]:
    data = await get_course_outcomes(scope, user, course_code)
    return success_response(data, request_id=get_request_id())


@curriculum_router.get(
    "/me/curriculum/courses/{course_code}/prerequisites",
    response_model=ApiResponse[PrerequisiteRead],
)
async def student_prerequisites_route(
    course_code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[PrerequisiteRead]:
    data = await get_prerequisites(scope, user, course_code)
    return success_response(data, request_id=get_request_id())


@curriculum_router.get(
    "/me/curriculum/courses/{course_code}/info",
    response_model=ApiResponse[CourseInfoRead],
)
async def student_course_info_route(
    course_code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[CourseInfoRead]:
    data = await get_course_information(scope, user, course_code)
    return success_response(data, request_id=get_request_id())


@curriculum_router.get("/me/curriculum/semester-subjects", response_model=ApiResponse[SemesterSubjectsRead])
async def student_semester_subjects_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[SemesterSubjectsRead]:
    data = await semester_subjects(scope, user)
    return success_response(data, request_id=get_request_id())


@curriculum_router.get("/me/registration/eligibility", response_model=ApiResponse[RegistrationEligibilityRead])
async def student_registration_eligibility_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[RegistrationEligibilityRead]:
    data = await get_registration_eligibility(scope, user)
    return success_response(data, request_id=get_request_id())


@curriculum_router.get(
    "/me/registration/overview-page",
    response_model=ApiResponse[RegistrationOverviewPageRead],
)
async def student_registration_overview_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[RegistrationOverviewPageRead]:
    data = await get_registration_overview_page(scope, user)
    return success_response(data, request_id=get_request_id())


@curriculum_router.get(
    "/me/registration/courses-page",
    response_model=ApiResponse[RegistrationCoursesPageRead],
)
async def student_registration_courses_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    semester: Annotated[str | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
    q: Annotated[str | None, Query(max_length=120)] = None,
) -> ApiResponse[RegistrationCoursesPageRead]:
    data = await get_registration_courses_page(scope, user, semester=semester, category=category, q=q)
    return success_response(data, request_id=get_request_id())


@curriculum_router.get(
    "/me/registration/courses/{course_code}/detail-page",
    response_model=ApiResponse[RegistrationCourseDetailPageRead],
)
async def student_registration_course_detail_page_route(
    course_code: Annotated[str, Path(description="Course code")],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[RegistrationCourseDetailPageRead]:
    data = await get_registration_course_detail_page(scope, user, course_code)
    return success_response(data, request_id=get_request_id())


@curriculum_router.get(
    "/me/registration/electives-page",
    response_model=ApiResponse[RegistrationElectivesPageRead],
)
async def student_registration_electives_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[RegistrationElectivesPageRead]:
    data = await get_registration_electives_page(scope, user)
    return success_response(data, request_id=get_request_id())


@curriculum_router.get(
    "/me/registration/review-page",
    response_model=ApiResponse[RegistrationReviewPageRead],
)
async def student_registration_review_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[RegistrationReviewPageRead]:
    data = await get_registration_review_page(scope, user)
    return success_response(data, request_id=get_request_id())


@curriculum_router.get(
    "/me/registration/status-page",
    response_model=ApiResponse[RegistrationStatusPageRead],
)
async def student_registration_status_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[RegistrationStatusPageRead]:
    data = await get_registration_status_page(scope, user)
    return success_response(data, request_id=get_request_id())


@curriculum_router.get("/me/registration/available-courses", response_model=ApiResponse[list[AvailableCourseRead]])
async def student_available_courses_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[AvailableCourseRead]]:
    data = await list_available_courses(scope, user)
    return success_response(data, request_id=get_request_id())


@curriculum_router.get("/me/registration/elective-groups", response_model=ApiResponse[list[ElectiveGroupRead]])
async def student_elective_groups_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[ElectiveGroupRead]]:
    data = await list_elective_groups(scope, user)
    return success_response(data, request_id=get_request_id())


@curriculum_router.get(
    "/me/registration/elective-groups/{group_id}/options",
    response_model=ApiResponse[list[ElectiveOptionRead]],
)
async def student_elective_options_route(
    group_id: Annotated[str, Path(description="Elective group id")],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[ElectiveOptionRead]]:
    data = await list_elective_options(scope, user, group_id)
    return success_response(data, request_id=get_request_id())


@curriculum_router.post("/me/registration/validate", response_model=ApiResponse[RegistrationValidationRead])
async def student_validate_registration_route(
    selections: list[RegistrationSelectionInput],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[RegistrationValidationRead]:
    data = await validate_course_selection(scope, user, selections)
    return success_response(data, request_id=get_request_id())


@curriculum_router.put("/me/registration/draft", response_model=ApiResponse[RegistrationSubmitRead])
async def student_save_registration_draft_route(
    selections: list[RegistrationSelectionInput],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[RegistrationSubmitRead]:
    data = await save_registration_draft(scope, user, selections)
    return success_response(data, request_id=get_request_id())


@curriculum_router.post("/me/registration/submit", response_model=ApiResponse[RegistrationSubmitRead])
async def student_submit_registration_route(
    selections: list[RegistrationSelectionInput],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    _: Annotated[None, Depends(enrollment_request_rate_limit)],
) -> ApiResponse[RegistrationSubmitRead]:
    data = await submit_registration(scope, user, selections)
    return success_response(data, request_id=get_request_id())


@curriculum_router.put(
    "/me/registration/requests/{request_id}",
    response_model=ApiResponse[RegistrationSubmitRead],
)
async def student_update_registration_route(
    request_id: str,
    selections: list[RegistrationSelectionInput],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    _: Annotated[None, Depends(enrollment_request_rate_limit)],
) -> ApiResponse[RegistrationSubmitRead]:
    data = await update_registration(scope, user, request_id, selections)
    return success_response(data, request_id=get_request_id())


@curriculum_router.post(
    "/me/registration/courses/{course_id}/cancel",
    response_model=ApiResponse[CourseRegistrationRead],
)
async def student_cancel_registration_route(
    course_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[CourseRegistrationRead]:
    data = await cancel_registration(scope, user, course_id)
    return success_response(data, request_id=get_request_id())


@curriculum_router.get("/me/registration/courses", response_model=ApiResponse[list[CourseRegistrationRead]])
async def student_confirmed_registrations_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[CourseRegistrationRead]]:
    data = await list_confirmed_registrations(scope, user)
    return success_response(data, request_id=get_request_id())


@curriculum_router.get(
    "/me/registration/requests/{request_id}",
    response_model=ApiResponse[RegistrationRequestRead],
)
async def student_registration_request_status_route(
    request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[RegistrationRequestRead]:
    data = await get_registration_request(scope, user, request_id)
    return success_response(data, request_id=get_request_id())


@curriculum_router.get("/me/registration/history", response_model=ApiResponse[Page[RegistrationHistoryRead]])
async def student_registration_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[RegistrationHistoryRead]]:
    data = await registration_history(scope, user, pagination)
    return success_response(data, request_id=get_request_id())
