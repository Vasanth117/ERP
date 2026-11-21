"""College admin academic configuration routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.ids import to_object_id
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_schemas import (
    AcademicCalendarCreate,
    AcademicCalendarRead,
    AcademicTermCreate,
    AcademicTermRead,
    AcademicYearCreate,
    AcademicYearRead,
    AcademicYearUpdate,
    ConfigHistoryRead,
    CourseAdminCreate,
    CourseAdminRead,
    ProgrammeCreate,
    ProgrammeRead,
    RegulationRead,
    RegulationUpsert,
    SectionCreate,
)
from app.modules.college_admin.academic_configuration_dashboard_page_service import (
    get_academic_configuration_dashboard_page,
)
from app.modules.college_admin.academic_year_management_page_service import (
    close_current_academic_year,
    create_academic_year_management,
    get_academic_year_management_page,
    save_academic_year_management_rules,
)
from app.modules.college_admin.course_curriculum_page_service import (
    get_course_configuration_page,
    get_curriculum_management_page,
    get_subject_management_page,
    save_course_configuration,
)
from app.modules.college_admin.programme_management_page_service import (
    create_programme_management,
    get_programme_management_page,
)
from app.modules.college_admin.semester_management_page_service import (
    create_semester_management_term,
    get_semester_management_page,
    save_semester_management_settings,
)
from app.modules.college_admin.academic_config_service import (
    configuration_history,
    create_academic_term,
    create_academic_year,
    create_calendar,
    create_course,
    create_section,
    list_academic_terms,
    list_academic_years,
    list_programmes,
    publish_academic_year,
    publish_calendar,
    publish_regulation,
    update_academic_year,
    upsert_programme,
    upsert_regulation,
)
from app.modules.college_admin.schemas import (
    AcademicConfigurationDashboardPageRead,
    AcademicYearManagementCreate,
    AcademicYearManagementPageRead,
    AcademicYearManagementRulesSave,
    CourseConfigurationPageRead,
    CourseConfigurationSave,
    CurriculumManagementPageRead,
    ProgrammeManagementCreate,
    ProgrammeManagementPageRead,
    SubjectManagementPageRead,
    SemesterManagementCreate,
    SemesterManagementPageRead,
    SemesterManagementSettingsSave,
)
from app.modules.college_admin.deps import college_admin_user

router = APIRouter()


@router.get(
    "/years/management/page",
    response_model=ApiResponse[AcademicYearManagementPageRead],
)
async def academic_year_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
) -> ApiResponse[AcademicYearManagementPageRead]:
    return success_response(
        await get_academic_year_management_page(scope, page=page),
        request_id=get_request_id(),
    )


@router.post(
    "/years/management/create",
    response_model=ApiResponse[AcademicYearManagementPageRead],
    status_code=status.HTTP_201_CREATED,
)
async def academic_year_management_create_route(
    payload: AcademicYearManagementCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AcademicYearManagementPageRead]:
    return success_response(
        await create_academic_year_management(scope, payload),
        request_id=get_request_id(),
    )


@router.post(
    "/years/management/close-current",
    response_model=ApiResponse[AcademicYearManagementPageRead],
)
async def academic_year_management_close_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AcademicYearManagementPageRead]:
    return success_response(
        await close_current_academic_year(scope),
        request_id=get_request_id(),
    )


@router.put(
    "/years/management/rules",
    response_model=ApiResponse[AcademicYearManagementPageRead],
)
async def academic_year_management_rules_route(
    payload: AcademicYearManagementRulesSave,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AcademicYearManagementPageRead]:
    return success_response(
        await save_academic_year_management_rules(scope, payload),
        request_id=get_request_id(),
    )


@router.get(
    "/semesters/management/page",
    response_model=ApiResponse[SemesterManagementPageRead],
)
async def semester_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    academic_year_id: Annotated[str | None, Query()] = None,
    term_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[SemesterManagementPageRead]:
    return success_response(
        await get_semester_management_page(
            scope,
            academic_year_id=academic_year_id,
            term_id=term_id,
        ),
        request_id=get_request_id(),
    )


@router.put(
    "/semesters/management/settings",
    response_model=ApiResponse[SemesterManagementPageRead],
)
async def semester_management_settings_route(
    payload: SemesterManagementSettingsSave,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[SemesterManagementPageRead]:
    return success_response(
        await save_semester_management_settings(scope, payload),
        request_id=get_request_id(),
    )


@router.get(
    "/programmes/management/page",
    response_model=ApiResponse[ProgrammeManagementPageRead],
)
async def programme_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    search: Annotated[str | None, Query()] = None,
    level_filter: Annotated[str | None, Query()] = None,
    department_id: Annotated[str | None, Query()] = None,
    regulation_filter: Annotated[str | None, Query()] = None,
    status_filter: Annotated[str | None, Query()] = None,
) -> ApiResponse[ProgrammeManagementPageRead]:
    return success_response(
        await get_programme_management_page(
            scope,
            page=page,
            search=search,
            level_filter=level_filter,
            department_id=department_id,
            regulation_filter=regulation_filter,
            status_filter=status_filter,
        ),
        request_id=get_request_id(),
    )


@router.post(
    "/programmes/management/create",
    response_model=ApiResponse[ProgrammeManagementPageRead],
    status_code=status.HTTP_201_CREATED,
)
async def programme_management_create_route(
    payload: ProgrammeManagementCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ProgrammeManagementPageRead]:
    return success_response(
        await create_programme_management(scope, payload),
        request_id=get_request_id(),
    )


@router.get(
    "/subjects/management/page",
    response_model=ApiResponse[SubjectManagementPageRead],
)
async def subject_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    search: Annotated[str | None, Query()] = None,
    department_id: Annotated[str | None, Query()] = None,
    type_filter: Annotated[str | None, Query()] = None,
    regulation_filter: Annotated[str | None, Query()] = None,
    semester_filter: Annotated[str | None, Query()] = None,
) -> ApiResponse[SubjectManagementPageRead]:
    return success_response(
        await get_subject_management_page(
            scope,
            page=page,
            search=search,
            department_id=department_id,
            type_filter=type_filter,
            regulation_filter=regulation_filter,
            semester_filter=semester_filter,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/curriculum/management/page",
    response_model=ApiResponse[CurriculumManagementPageRead],
)
async def curriculum_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    programme_id: Annotated[str | None, Query()] = None,
    semester: Annotated[int, Query(ge=1, le=12)] = 4,
) -> ApiResponse[CurriculumManagementPageRead]:
    return success_response(
        await get_curriculum_management_page(scope, programme_id=programme_id, semester=semester),
        request_id=get_request_id(),
    )


@router.get(
    "/courses/configuration/page",
    response_model=ApiResponse[CourseConfigurationPageRead],
)
async def course_configuration_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    course_id: Annotated[str | None, Query()] = None,
    mode: Annotated[str | None, Query()] = None,
) -> ApiResponse[CourseConfigurationPageRead]:
    return success_response(
        await get_course_configuration_page(scope, course_id=course_id, mode=mode),
        request_id=get_request_id(),
    )


@router.put(
    "/courses/configuration/save",
    response_model=ApiResponse[CourseConfigurationPageRead],
)
async def course_configuration_save_route(
    payload: CourseConfigurationSave,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[CourseConfigurationPageRead]:
    return success_response(
        await save_course_configuration(scope, payload),
        request_id=get_request_id(),
    )


@router.post(
    "/semesters/management/create",
    response_model=ApiResponse[SemesterManagementPageRead],
    status_code=status.HTTP_201_CREATED,
)
async def semester_management_create_route(
    payload: SemesterManagementCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[SemesterManagementPageRead]:
    return success_response(
        await create_semester_management_term(scope, payload),
        request_id=get_request_id(),
    )


@router.get(
    "/configuration-dashboard/page",
    response_model=ApiResponse[AcademicConfigurationDashboardPageRead],
)
async def academic_configuration_dashboard_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AcademicConfigurationDashboardPageRead]:
    return success_response(
        await get_academic_configuration_dashboard_page(scope),
        request_id=get_request_id(),
    )


@router.get("/years", response_model=ApiResponse[list[AcademicYearRead]])
async def list_years_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[AcademicYearRead]]:
    return success_response(await list_academic_years(scope), request_id=get_request_id())


@router.post("/years", response_model=ApiResponse[AcademicYearRead], status_code=status.HTTP_201_CREATED)
async def create_year_route(
    payload: AcademicYearCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AcademicYearRead]:
    return success_response(await create_academic_year(scope, payload), request_id=get_request_id())


@router.patch("/years/{year_id}", response_model=ApiResponse[AcademicYearRead])
async def update_year_route(
    year_id: str,
    payload: AcademicYearUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AcademicYearRead]:
    return success_response(await update_academic_year(scope, to_object_id(year_id, "year_id"), payload), request_id=get_request_id())


@router.post("/years/{year_id}/publish", response_model=ApiResponse[AcademicYearRead])
async def publish_year_route(
    year_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AcademicYearRead]:
    return success_response(await publish_academic_year(scope, to_object_id(year_id, "year_id")), request_id=get_request_id())


@router.post("/terms", response_model=ApiResponse[AcademicTermRead], status_code=status.HTTP_201_CREATED)
async def create_term_route(
    payload: AcademicTermCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AcademicTermRead]:
    return success_response(await create_academic_term(scope, payload), request_id=get_request_id())


@router.get("/terms", response_model=ApiResponse[list[AcademicTermRead]])
async def list_terms_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    academic_year_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[list[AcademicTermRead]]:
    return success_response(await list_academic_terms(scope, academic_year_id=academic_year_id), request_id=get_request_id())


@router.post("/calendars", response_model=ApiResponse[AcademicCalendarRead], status_code=status.HTTP_201_CREATED)
async def create_calendar_route(
    payload: AcademicCalendarCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AcademicCalendarRead]:
    return success_response(await create_calendar(scope, payload), request_id=get_request_id())


@router.post("/calendars/{calendar_id}/publish", response_model=ApiResponse[AcademicCalendarRead])
async def publish_calendar_route(
    calendar_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AcademicCalendarRead]:
    return success_response(await publish_calendar(scope, to_object_id(calendar_id, "calendar id")), request_id=get_request_id())


@router.post("/programmes", response_model=ApiResponse[ProgrammeRead], status_code=status.HTTP_201_CREATED)
async def upsert_programme_route(
    payload: ProgrammeCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ProgrammeRead]:
    return success_response(await upsert_programme(scope, payload), request_id=get_request_id())


@router.get("/programmes", response_model=ApiResponse[list[ProgrammeRead]])
async def list_programmes_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[ProgrammeRead]]:
    return success_response(await list_programmes(scope), request_id=get_request_id())


@router.put("/regulations", response_model=ApiResponse[RegulationRead])
async def upsert_regulation_route(
    payload: RegulationUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[RegulationRead]:
    return success_response(await upsert_regulation(scope, payload), request_id=get_request_id())


@router.post("/regulations/{regulation_id}/publish", response_model=ApiResponse[RegulationRead])
async def publish_regulation_route(
    regulation_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[RegulationRead]:
    return success_response(await publish_regulation(scope, to_object_id(regulation_id, "regulation id")), request_id=get_request_id())


@router.post("/courses", response_model=ApiResponse[CourseAdminRead], status_code=status.HTTP_201_CREATED)
async def create_course_route(
    payload: CourseAdminCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[CourseAdminRead]:
    return success_response(await create_course(scope, payload), request_id=get_request_id())


@router.post("/sections", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def create_section_route(
    payload: SectionCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await create_section(scope, payload), request_id=get_request_id())


@router.get("/configuration-history", response_model=ApiResponse[list[ConfigHistoryRead]])
async def config_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[ConfigHistoryRead]]:
    return success_response(await configuration_history(scope), request_id=get_request_id())
