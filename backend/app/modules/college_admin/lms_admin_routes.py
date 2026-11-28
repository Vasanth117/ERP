"""LMS administration routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.college_admin.deps import college_admin_user
from app.modules.college_admin.lms_progress_faculty_page_service import (
    approve_selected_faculty_content,
    get_lms_faculty_content_management_page,
    get_lms_student_learning_progress_page,
)
from app.modules.college_admin.lms_assessments_page_service import (
    get_lms_assessment_management_page,
    get_lms_assignment_management_page,
    get_lms_quiz_management_page,
)
from app.modules.college_admin.lms_content_admin_service import (
    export_lms_learning_materials_csv,
    export_lms_units_chapters_csv,
    export_lms_video_lectures_csv,
    upload_lms_content_material,
)
from app.modules.college_admin.lms_content_page_service import (
    get_lms_learning_material_management_page,
    get_lms_video_lecture_management_page,
)
from app.modules.college_admin.lms_unit_chapter_page_service import get_lms_unit_chapter_management_page
from app.modules.college_admin.lms_courses_mapping_page_service import (
    auto_map_lms_subject_courses,
    get_lms_course_management_page,
    get_lms_subject_course_mapping_page,
    save_lms_subject_mappings,
)
from app.modules.college_admin.schemas import (
    LmsAssessmentManagementPageRead,
    LmsAssignmentManagementPageRead,
    LmsCourseManagementPageRead,
    LmsDashboardPageRead,
    LmsLearningMaterialManagementPageRead,
    LmsUnitChapterManagementPageRead,
    LmsFacultyContentManagementPageRead,
    LmsQuizManagementPageRead,
    LmsReportScheduleCreate,
    LmsReportsPageRead,
    LmsSettingsPageRead,
    LmsSettingsSave,
    LmsSectionSubNavRead,
    LmsStudentLearningProgressPageRead,
    LmsSubjectCourseMappingPageRead,
    LmsVideoLectureManagementPageRead,
)
from app.modules.college_admin.lms_admin_schemas import (
    LmsConfigurationHistoryItem,
    LmsContentCategoryRead,
    LmsContentCategoryUpsert,
    LmsCourseMappingRead,
    LmsCourseMappingUpsert,
    LmsMonitorSummary,
    LmsOperationalStats,
    LmsPublishingPolicyRead,
    LmsPublishingPolicyUpsert,
    LmsSettingsRead,
    LmsSettingsUpdate,
)
from app.modules.college_admin.lms_dashboard_page_service import get_lms_dashboard_page
from app.modules.college_admin.lms_reports_page_service import create_lms_report_schedule, get_lms_reports_page
from app.modules.college_admin.lms_settings_page_service import (
    get_lms_settings_management_page,
    save_lms_settings_management_page,
)
from app.modules.college_admin.lms_section_sub_nav_service import get_lms_section_sub_nav
from app.modules.college_admin.lms_admin_service import (
    get_lms_integration_status,
    get_lms_monitor_summary,
    get_lms_operational_stats,
    get_lms_settings,
    list_content_categories,
    list_course_mappings,
    list_lms_configuration_history,
    update_lms_settings,
    upsert_content_category,
    upsert_course_mapping,
    upsert_publishing_policy,
)

router = APIRouter()


@router.get("/navigation/section-sub-nav", response_model=ApiResponse[LmsSectionSubNavRead])
async def lms_section_sub_nav_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    path: Annotated[str, Query()],
):
    return success_response(await get_lms_section_sub_nav(scope, path=path), request_id=get_request_id())


@router.get("/courses/management/page", response_model=ApiResponse[LmsCourseManagementPageRead])
async def lms_course_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 4,
    search: Annotated[str | None, Query()] = None,
    department: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
):
    return success_response(
        await get_lms_course_management_page(
            scope,
            page=page,
            page_size=page_size,
            search=search,
            department=department,
            status=status,
        ),
        request_id=get_request_id(),
    )


@router.get("/subject-mapping/management/page", response_model=ApiResponse[LmsSubjectCourseMappingPageRead])
async def lms_subject_course_mapping_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
):
    return success_response(
        await get_lms_subject_course_mapping_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.post("/subject-mapping/auto-map", response_model=ApiResponse[dict])
async def lms_subject_auto_map_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
):
    return success_response(await auto_map_lms_subject_courses(scope), request_id=get_request_id())


@router.post("/subject-mapping/save", response_model=ApiResponse[dict])
async def lms_subject_save_mapping_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
):
    return success_response(await save_lms_subject_mappings(scope), request_id=get_request_id())


@router.get("/student-progress/management/page", response_model=ApiResponse[LmsStudentLearningProgressPageRead])
async def lms_student_learning_progress_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
):
    return success_response(
        await get_lms_student_learning_progress_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/faculty-content/management/page", response_model=ApiResponse[LmsFacultyContentManagementPageRead])
async def lms_faculty_content_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
):
    return success_response(
        await get_lms_faculty_content_management_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.post("/faculty-content/approve-selected", response_model=ApiResponse[dict])
async def lms_faculty_content_approve_selected_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
):
    return success_response(await approve_selected_faculty_content(scope), request_id=get_request_id())


@router.get("/assignments/management/page", response_model=ApiResponse[LmsAssignmentManagementPageRead])
async def lms_assignment_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
):
    return success_response(
        await get_lms_assignment_management_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/quizzes/management/page", response_model=ApiResponse[LmsQuizManagementPageRead])
async def lms_quiz_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
):
    return success_response(
        await get_lms_quiz_management_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/assessments/management/page", response_model=ApiResponse[LmsAssessmentManagementPageRead])
async def lms_assessment_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
):
    return success_response(
        await get_lms_assessment_management_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/units-chapters/management/page", response_model=ApiResponse[LmsUnitChapterManagementPageRead])
async def lms_unit_chapter_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    course_code: Annotated[str | None, Query()] = None,
):
    return success_response(
        await get_lms_unit_chapter_management_page(scope, course_code=course_code),
        request_id=get_request_id(),
    )


@router.get("/units-chapters/management/export")
async def lms_unit_chapter_management_export_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    course_code: Annotated[str | None, Query()] = None,
):
    csv_text = await export_lms_units_chapters_csv(scope, course_code=course_code)
    suffix = f"-{course_code.upper()}" if course_code else ""
    return PlainTextResponse(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="lms-units-chapters{suffix}.csv"'},
    )


@router.post("/learning-materials/management/upload", response_model=ApiResponse[dict])
async def lms_learning_material_upload_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
    course_code: Annotated[str, Form()],
    title: Annotated[str, Form()],
    unit_no: Annotated[int | None, Form()] = None,
    material_kind: Annotated[str, Form()] = "document",
    file: UploadFile = File(...),
):
    try:
        payload = await upload_lms_content_material(
            scope,
            user,
            course_code=course_code,
            title=title,
            unit_no=unit_no,
            material_kind=material_kind,
            upload=file,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return success_response(payload, request_id=get_request_id())


@router.get("/learning-materials/management/export")
async def lms_learning_material_management_export_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
):
    return PlainTextResponse(
        content=await export_lms_learning_materials_csv(scope),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="lms-learning-materials.csv"'},
    )


@router.get("/video-lectures/management/export")
async def lms_video_lecture_management_export_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
):
    return PlainTextResponse(
        content=await export_lms_video_lectures_csv(scope),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="lms-video-lectures.csv"'},
    )


@router.get("/learning-materials/management/page", response_model=ApiResponse[LmsLearningMaterialManagementPageRead])
async def lms_learning_material_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
):
    return success_response(
        await get_lms_learning_material_management_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/video-lectures/management/page", response_model=ApiResponse[LmsVideoLectureManagementPageRead])
async def lms_video_lecture_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
):
    return success_response(
        await get_lms_video_lecture_management_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/dashboard/page", response_model=ApiResponse[LmsDashboardPageRead])
async def lms_dashboard_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 4,
):
    return success_response(
        await get_lms_dashboard_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/reports/management/page", response_model=ApiResponse[LmsReportsPageRead])
async def lms_reports_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
):
    return success_response(
        await get_lms_reports_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.post("/reports/management/page", response_model=ApiResponse[LmsReportsPageRead])
async def lms_reports_schedule_create_route(
    payload: LmsReportScheduleCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
):
    return success_response(
        await create_lms_report_schedule(scope, payload, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/settings/management/page", response_model=ApiResponse[LmsSettingsPageRead])
async def lms_settings_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
):
    return success_response(await get_lms_settings_management_page(scope), request_id=get_request_id())


@router.put("/settings/management/page", response_model=ApiResponse[LmsSettingsPageRead])
async def lms_settings_management_save_route(
    payload: LmsSettingsSave,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
):
    return success_response(
        await save_lms_settings_management_page(scope, user, payload),
        request_id=get_request_id(),
    )


@router.get("/settings", response_model=ApiResponse[LmsSettingsRead])
async def lms_settings_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[LmsSettingsRead]:
    return success_response(await get_lms_settings(scope), request_id=get_request_id())


@router.patch("/settings", response_model=ApiResponse[LmsSettingsRead])
async def lms_settings_update_route(
    payload: LmsSettingsUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[LmsSettingsRead]:
    return success_response(await update_lms_settings(scope, user, payload), request_id=get_request_id())


@router.get("/course-mappings", response_model=ApiResponse[list[LmsCourseMappingRead]])
async def lms_course_mappings_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[LmsCourseMappingRead]]:
    return success_response(await list_course_mappings(scope), request_id=get_request_id())


@router.put("/course-mappings", response_model=ApiResponse[LmsCourseMappingRead])
async def lms_course_mapping_upsert_route(
    payload: LmsCourseMappingUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[LmsCourseMappingRead]:
    return success_response(await upsert_course_mapping(scope, user, payload), request_id=get_request_id())


@router.get("/content-categories", response_model=ApiResponse[list[LmsContentCategoryRead]])
async def lms_categories_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[LmsContentCategoryRead]]:
    return success_response(await list_content_categories(scope), request_id=get_request_id())


@router.put("/content-categories", response_model=ApiResponse[LmsContentCategoryRead])
async def lms_category_upsert_route(
    payload: LmsContentCategoryUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[LmsContentCategoryRead]:
    return success_response(await upsert_content_category(scope, payload), request_id=get_request_id())


@router.put("/publishing-policies", response_model=ApiResponse[LmsPublishingPolicyRead])
async def lms_publishing_policy_route(
    payload: LmsPublishingPolicyUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[LmsPublishingPolicyRead]:
    return success_response(await upsert_publishing_policy(scope, user, payload), request_id=get_request_id())


@router.get("/statistics", response_model=ApiResponse[LmsOperationalStats])
async def lms_statistics_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[LmsOperationalStats]:
    return success_response(await get_lms_operational_stats(scope), request_id=get_request_id())


@router.get("/monitoring", response_model=ApiResponse[LmsMonitorSummary])
async def lms_monitor_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[LmsMonitorSummary]:
    return success_response(await get_lms_monitor_summary(scope), request_id=get_request_id())


@router.get("/configuration-history", response_model=ApiResponse[list[LmsConfigurationHistoryItem]])
async def lms_config_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[LmsConfigurationHistoryItem]]:
    return success_response(await list_lms_configuration_history(scope), request_id=get_request_id())


@router.get("/integrations", response_model=ApiResponse[dict])
async def lms_integrations_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await get_lms_integration_status(scope), request_id=get_request_id())