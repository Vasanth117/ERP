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
from app.modules.college_admin.deps import college_admin_user

router = APIRouter()


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
