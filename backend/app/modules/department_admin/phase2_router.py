"""Department Admin phase 2 routes — faculty and academic."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.department_admin.academic_management_service import (
    academic_progression,
    create_programme,
    curriculum_coverage,
    get_programme,
    list_course_offerings,
    list_curricula,
    list_programmes,
    list_subjects,
    request_course_offering,
    update_programme,
)
from app.modules.department_admin.deps import department_admin_user
from app.modules.department_admin.faculty_management_service import (
    create_faculty_assignment_request,
    create_substitute_request,
    create_teaching_assignment,
    get_faculty_availability,
    get_faculty_profile_detail,
    get_faculty_workload,
    list_faculty_directory,
    list_substitute_requests,
    list_teaching_assignments,
    list_unassigned_subjects,
    update_teaching_assignment,
)
from app.modules.department_admin.phase2_schemas import (
    AcademicProgressionSummary,
    CourseOfferingRead,
    CourseOfferingRequestCreate,
    CurriculumCoverageItem,
    CurriculumRead,
    FacultyAssignmentRequestCreate,
    FacultyAvailabilityRead,
    FacultyDirectoryFilters,
    FacultyDirectoryItem,
    FacultyProfileDetailRead,
    FacultyWorkloadRead,
    ProgrammeCreate,
    ProgrammeRead,
    ProgrammeUpdate,
    SubstituteRequestCreate,
    SubstituteRequestRead,
    SubjectRead,
    TeachingAssignmentCreate,
    TeachingAssignmentRead,
    TeachingAssignmentUpdate,
    UnassignedSubjectItem,
)

phase2_router = APIRouter()


@phase2_router.get("/faculty", response_model=ApiResponse[Page[FacultyDirectoryItem]])
async def faculty_directory_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    designation: Annotated[str | None, Query()] = None,
    employment_status: Annotated[str | None, Query()] = None,
    programme_code: Annotated[str | None, Query()] = None,
    subject_code: Annotated[str | None, Query()] = None,
    academic_year_label: Annotated[str | None, Query()] = None,
    semester_label: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[FacultyDirectoryItem]]:
    filters = FacultyDirectoryFilters(
        designation=designation,
        employment_status=employment_status,
        programme_code=programme_code,
        subject_code=subject_code,
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        search=search,
    )
    data = await list_faculty_directory(scope, user, pagination=pagination, filters=filters)
    return success_response(data, request_id=get_request_id())


@phase2_router.get("/faculty/assignments", response_model=ApiResponse[Page[TeachingAssignmentRead]])
async def faculty_assignments_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    academic_year_label: Annotated[str | None, Query()] = None,
    semester_label: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[TeachingAssignmentRead]]:
    data = await list_teaching_assignments(
        scope, user, pagination=pagination, academic_year_label=academic_year_label, semester_label=semester_label
    )
    return success_response(data, request_id=get_request_id())


@phase2_router.post("/faculty/assignments", response_model=ApiResponse[TeachingAssignmentRead])
async def faculty_assignments_create_route(
    payload: TeachingAssignmentCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[TeachingAssignmentRead]:
    data = await create_teaching_assignment(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@phase2_router.patch("/faculty/assignments/{assignment_id}", response_model=ApiResponse[TeachingAssignmentRead])
async def faculty_assignments_update_route(
    assignment_id: str,
    payload: TeachingAssignmentUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[TeachingAssignmentRead]:
    data = await update_teaching_assignment(scope, user, assignment_id, payload)
    return success_response(data, request_id=get_request_id())


@phase2_router.get("/faculty/unassigned-subjects", response_model=ApiResponse[list[UnassignedSubjectItem]])
async def faculty_unassigned_subjects_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    academic_year_label: Annotated[str | None, Query()] = None,
    semester_label: Annotated[str | None, Query()] = None,
) -> ApiResponse[list[UnassignedSubjectItem]]:
    data = await list_unassigned_subjects(scope, user, academic_year_label=academic_year_label, semester_label=semester_label)
    return success_response(data, request_id=get_request_id())


@phase2_router.post("/faculty/assignment-requests", response_model=ApiResponse[dict])
async def faculty_assignment_request_route(
    payload: FacultyAssignmentRequestCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[dict]:
    data = await create_faculty_assignment_request(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@phase2_router.post("/faculty/substitute-requests", response_model=ApiResponse[SubstituteRequestRead])
async def substitute_request_create_route(
    payload: SubstituteRequestCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[SubstituteRequestRead]:
    data = await create_substitute_request(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@phase2_router.get("/faculty/substitute-requests", response_model=ApiResponse[Page[SubstituteRequestRead]])
async def substitute_requests_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[SubstituteRequestRead]]:
    data = await list_substitute_requests(scope, user, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@phase2_router.get("/faculty/{faculty_id}", response_model=ApiResponse[FacultyProfileDetailRead])
async def faculty_detail_route(
    faculty_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[FacultyProfileDetailRead]:
    data = await get_faculty_profile_detail(scope, user, faculty_id)
    return success_response(data, request_id=get_request_id())


@phase2_router.get("/faculty/{faculty_id}/availability", response_model=ApiResponse[FacultyAvailabilityRead])
async def faculty_availability_route(
    faculty_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    anchor_date: Annotated[date | None, Query()] = None,
) -> ApiResponse[FacultyAvailabilityRead]:
    data = await get_faculty_availability(scope, user, faculty_id, anchor=anchor_date)
    return success_response(data, request_id=get_request_id())


@phase2_router.get("/faculty/{faculty_id}/workload", response_model=ApiResponse[FacultyWorkloadRead])
async def faculty_workload_route(
    faculty_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    academic_year_label: Annotated[str, Query()],
    semester_label: Annotated[str, Query()],
) -> ApiResponse[FacultyWorkloadRead]:
    data = await get_faculty_workload(
        scope, user, faculty_id, academic_year_label=academic_year_label, semester_label=semester_label
    )
    return success_response(data, request_id=get_request_id())


@phase2_router.get("/programmes", response_model=ApiResponse[Page[ProgrammeRead]])
async def programmes_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ProgrammeRead]]:
    data = await list_programmes(scope, user, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@phase2_router.post("/programmes", response_model=ApiResponse[ProgrammeRead])
async def programmes_create_route(
    payload: ProgrammeCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[ProgrammeRead]:
    data = await create_programme(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@phase2_router.get("/programmes/{programme_id}", response_model=ApiResponse[ProgrammeRead])
async def programme_get_route(
    programme_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[ProgrammeRead]:
    data = await get_programme(scope, user, programme_id)
    return success_response(data, request_id=get_request_id())


@phase2_router.patch("/programmes/{programme_id}", response_model=ApiResponse[ProgrammeRead])
async def programme_update_route(
    programme_id: str,
    payload: ProgrammeUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[ProgrammeRead]:
    data = await update_programme(scope, user, programme_id, payload)
    return success_response(data, request_id=get_request_id())


@phase2_router.get("/curricula", response_model=ApiResponse[list[CurriculumRead]])
async def curricula_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    academic_year_label: Annotated[str | None, Query()] = None,
    semester_label: Annotated[str | None, Query()] = None,
) -> ApiResponse[list[CurriculumRead]]:
    data = await list_curricula(scope, user, academic_year_label=academic_year_label, semester_label=semester_label)
    return success_response(data, request_id=get_request_id())


@phase2_router.get("/subjects", response_model=ApiResponse[list[SubjectRead]])
async def subjects_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[list[SubjectRead]]:
    data = await list_subjects(scope, user)
    return success_response(data, request_id=get_request_id())


@phase2_router.get("/course-offerings", response_model=ApiResponse[list[CourseOfferingRead]])
async def course_offerings_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    academic_year_label: Annotated[str | None, Query()] = None,
    semester_label: Annotated[str | None, Query()] = None,
) -> ApiResponse[list[CourseOfferingRead]]:
    data = await list_course_offerings(scope, user, academic_year_label=academic_year_label, semester_label=semester_label)
    return success_response(data, request_id=get_request_id())


@phase2_router.post("/course-offerings", response_model=ApiResponse[dict])
async def course_offering_request_route(
    payload: CourseOfferingRequestCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[dict]:
    data = await request_course_offering(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@phase2_router.get("/curriculum-coverage", response_model=ApiResponse[list[CurriculumCoverageItem]])
async def curriculum_coverage_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[list[CurriculumCoverageItem]]:
    data = await curriculum_coverage(scope, user)
    return success_response(data, request_id=get_request_id())


@phase2_router.get("/academic-progression", response_model=ApiResponse[list[AcademicProgressionSummary]])
async def academic_progression_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[list[AcademicProgressionSummary]]:
    data = await academic_progression(scope, user)
    return success_response(data, request_id=get_request_id())