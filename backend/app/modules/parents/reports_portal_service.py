"""Consolidated parent reports (published / authorized data only)."""

import secrets
from datetime import datetime, timezone

from beanie import PydanticObjectId

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.parents.academic_overview_service import get_academic_overview
from app.modules.parents.attendance_monitoring_service import get_attendance_dashboard
from app.modules.parents.communication_portal_service import get_communication_dashboard
from app.modules.parents.enums import ParentDataPermission, ParentReportCategory
from app.modules.parents.examination_portal_service import get_examination_overview
from app.modules.parents.finance_portal_service import get_finance_dashboard, get_fee_statement
from app.modules.parents.meeting_portal_service import get_meeting_dashboard
from app.modules.parents.models import ParentReportAccessHistory
from app.modules.parents.phase5_schemas import ParentReportExportRead, ParentReportsDashboardRead
from app.modules.parents.policy import require_parent_scope
from app.modules.parents.repositories import ParentRelationshipRepository
from app.modules.parents.relationship_access import require_student_access
from app.modules.parents.student_context import resolve_student_for_parent
from app.modules.parents.student_services_portal_service import services_overview

_relationship_repo = ParentRelationshipRepository()


async def reports_dashboard(scope: AccessScope, parent: User) -> ParentReportsDashboardRead:
    authorize(scope, Permission.PARENT_REPORTS_READ)
    tenant_id = require_parent_scope(scope)
    rels = await _relationship_repo.list_active_for_parent(tenant_id, parent.id)
    return ParentReportsDashboardRead(
        linked_students=len(rels),
        categories_available=[c.value for c in ParentReportCategory],
    )


async def build_report(
    scope: AccessScope,
    parent: User,
    *,
    student_user_id: str | None,
    category: ParentReportCategory,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
    export_format: str = "json",
) -> ParentReportExportRead:
    authorize(scope, Permission.PARENT_REPORTS_READ)
    tenant_id = require_parent_scope(scope)
    payload: dict = {"category": category.value, "generated_at": utcnow().isoformat()}
    sid: PydanticObjectId | None = None
    if student_user_id:
        sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_PROFILE)
        payload["student_user_id"] = student_user_id

    if category == ParentReportCategory.ACADEMIC and sid:
        await require_student_access(tenant_id, parent.id, sid, ParentDataPermission.VIEW_RESULTS)
        overview = await get_academic_overview(scope, parent, student_user_id)
        payload["academic"] = overview.model_dump(mode="json")
    elif category == ParentReportCategory.ATTENDANCE and sid:
        await require_student_access(tenant_id, parent.id, sid, ParentDataPermission.VIEW_ATTENDANCE)
        dash = await get_attendance_dashboard(
            scope, parent, student_user_id, academic_year_label=academic_year_label, semester_label=semester_label
        )
        payload["attendance"] = dash.model_dump(mode="json")
    elif category == ParentReportCategory.EXAMINATION and sid:
        await require_student_access(tenant_id, parent.id, sid, ParentDataPermission.VIEW_EXAM_TIMETABLE)
        payload["examination"] = (await get_examination_overview(scope, parent, student_user_id)).model_dump(mode="json")
    elif category == ParentReportCategory.FINANCE and sid:
        await require_student_access(tenant_id, parent.id, sid, ParentDataPermission.VIEW_FEES)
        payload["finance"] = {
            "dashboard": (await get_finance_dashboard(scope, parent, student_user_id)).model_dump(mode="json"),
            "statement": (await get_fee_statement(scope, parent, student_user_id)).model_dump(mode="json"),
        }
    elif category == ParentReportCategory.STUDENT_SERVICES and sid:
        payload["services"] = (await services_overview(scope, parent, student_user_id)).model_dump(mode="json")
    elif category == ParentReportCategory.PARENT_ACTIVITY:
        payload["communications"] = (await get_communication_dashboard(scope, parent)).model_dump(mode="json")
        if sid:
            payload["meetings"] = (
                await get_meeting_dashboard(scope, parent, student_user_id=student_user_id)
            ).model_dump(mode="json")
    elif category == ParentReportCategory.CONSOLIDATED:
        if not student_user_id:
            raise AppError(code="VALIDATION_ERROR", message="Student required for consolidated report", status_code=422)
        sections: dict = {}
        _, perms = await require_student_access(tenant_id, parent.id, sid, None)
        grants = perms.grants if perms else {}
        if grants.get(ParentDataPermission.VIEW_RESULTS.value):
            sections["academic"] = (await get_academic_overview(scope, parent, student_user_id)).model_dump(mode="json")
        if grants.get(ParentDataPermission.VIEW_ATTENDANCE.value):
            sections["attendance"] = (
                await get_attendance_dashboard(scope, parent, student_user_id)
            ).model_dump(mode="json")
        if grants.get(ParentDataPermission.VIEW_FEES.value):
            sections["finance"] = (await get_finance_dashboard(scope, parent, student_user_id)).model_dump(mode="json")
        payload["sections"] = sections
    else:
        raise AppError(code="VALIDATION_ERROR", message="Unsupported report category", status_code=422)

    token = secrets.token_urlsafe(24)
    await ParentReportAccessHistory(
        tenant_id=tenant_id,
        parent_user_id=parent.id,
        student_user_id=sid,
        report_category=category.value,
        export_format=export_format,
        filter_summary={
            "academic_year_label": academic_year_label,
            "semester_label": semester_label,
        },
    ).insert()
    return ParentReportExportRead(
        report_category=category.value,
        student_user_id=student_user_id,
        generated_at=utcnow(),
        export_token=token,
        format=export_format,
        payload=payload,
    )