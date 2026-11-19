"""Examination cell authorization."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.core.exceptions import AppError
from app.modules.tenants.models import Department


def _has_dashboard_read(scope: AccessScope) -> bool:
    return (
        Permission.EXAMINATION_CELL_DASHBOARD_READ in scope.effective_permissions
        or Permission.EXAMINATION_ADMIN_READ in scope.effective_permissions
    )


def _has_session_read(scope: AccessScope) -> bool:
    return (
        Permission.EXAMINATION_CELL_SESSION_READ in scope.effective_permissions
        or Permission.EXAMINATION_ADMIN_READ in scope.effective_permissions
    )


def _has_session_manage(scope: AccessScope) -> bool:
    return (
        Permission.EXAMINATION_CELL_SESSION_MANAGE in scope.effective_permissions
        or Permission.EXAMINATION_ADMIN_CONFIG in scope.effective_permissions
    )


def authorize_examination_cell_dashboard(scope: AccessScope) -> None:
    if _has_dashboard_read(scope):
        return
    authorize(scope, Permission.EXAMINATION_CELL_DASHBOARD_READ)


def authorize_examination_cell_read(scope: AccessScope) -> None:
    if _has_session_read(scope) or _has_dashboard_read(scope):
        return
    authorize(scope, Permission.EXAMINATION_CELL_SESSION_READ)


def authorize_examination_cell_manage(scope: AccessScope) -> None:
    if _has_session_manage(scope):
        return
    authorize(scope, Permission.EXAMINATION_CELL_SESSION_MANAGE)


def _has_assessment_read(scope: AccessScope) -> bool:
    return (
        Permission.EXAMINATION_CELL_ASSESSMENT_READ in scope.effective_permissions
        or Permission.EXAMINATION_ADMIN_READ in scope.effective_permissions
    )


def _has_assessment_manage(scope: AccessScope) -> bool:
    return (
        Permission.EXAMINATION_CELL_ASSESSMENT_MANAGE in scope.effective_permissions
        or Permission.EXAMINATION_ADMIN_CONFIG in scope.effective_permissions
    )


def _has_timetable_read(scope: AccessScope) -> bool:
    return (
        Permission.EXAMINATION_CELL_TIMETABLE_READ in scope.effective_permissions
        or Permission.EXAMINATION_ADMIN_READ in scope.effective_permissions
    )


def _has_timetable_manage(scope: AccessScope) -> bool:
    return (
        Permission.EXAMINATION_CELL_TIMETABLE_MANAGE in scope.effective_permissions
        or Permission.EXAMINATION_ADMIN_CONFIG in scope.effective_permissions
    )


def authorize_examination_cell_assessment_read(scope: AccessScope) -> None:
    if _has_assessment_read(scope) or _has_assessment_manage(scope):
        return
    authorize(scope, Permission.EXAMINATION_CELL_ASSESSMENT_READ)


def authorize_examination_cell_assessment_manage(scope: AccessScope) -> None:
    if _has_assessment_manage(scope):
        return
    authorize(scope, Permission.EXAMINATION_CELL_ASSESSMENT_MANAGE)


def authorize_examination_cell_timetable_read(scope: AccessScope) -> None:
    if _has_timetable_read(scope) or _has_timetable_manage(scope):
        return
    authorize(scope, Permission.EXAMINATION_CELL_TIMETABLE_READ)


def authorize_examination_cell_timetable_manage(scope: AccessScope) -> None:
    if _has_timetable_manage(scope):
        return
    authorize(scope, Permission.EXAMINATION_CELL_TIMETABLE_MANAGE)


def authorize_examination_cell_timetable_approve(scope: AccessScope) -> None:
    if Permission.EXAMINATION_CELL_TIMETABLE_APPROVE in scope.effective_permissions or Permission.EXAMINATION_ADMIN_PUBLISH in scope.effective_permissions:
        return
    authorize(scope, Permission.EXAMINATION_CELL_TIMETABLE_APPROVE)


def authorize_examination_cell_timetable_publish(scope: AccessScope) -> None:
    if Permission.EXAMINATION_CELL_TIMETABLE_PUBLISH in scope.effective_permissions or Permission.EXAMINATION_ADMIN_PUBLISH in scope.effective_permissions:
        return
    authorize(scope, Permission.EXAMINATION_CELL_TIMETABLE_PUBLISH)


def _has_eligibility_manage(scope: AccessScope) -> bool:
    return (
        Permission.EXAMINATION_CELL_ELIGIBILITY_MANAGE in scope.effective_permissions
        or Permission.EXAMINATION_ADMIN_CONFIG in scope.effective_permissions
    )


def authorize_examination_cell_eligibility_manage(scope: AccessScope) -> None:
    if _has_eligibility_manage(scope):
        return
    authorize(scope, Permission.EXAMINATION_CELL_ELIGIBILITY_MANAGE)


def _has_registration_manage(scope: AccessScope) -> bool:
    return (
        Permission.EXAMINATION_CELL_REGISTRATION_MANAGE in scope.effective_permissions
        or Permission.EXAMINATION_ADMIN_CONFIG in scope.effective_permissions
    )


def authorize_examination_cell_registration_manage(scope: AccessScope) -> None:
    if _has_registration_manage(scope):
        return
    authorize(scope, Permission.EXAMINATION_CELL_REGISTRATION_MANAGE)


def _has_hall_ticket_manage(scope: AccessScope) -> bool:
    return (
        Permission.EXAMINATION_CELL_HALL_TICKET_MANAGE in scope.effective_permissions
        or Permission.EXAMINATION_ADMIN_CONFIG in scope.effective_permissions
    )


def authorize_examination_cell_hall_ticket_manage(scope: AccessScope) -> None:
    if _has_hall_ticket_manage(scope):
        return
    authorize(scope, Permission.EXAMINATION_CELL_HALL_TICKET_MANAGE)


def authorize_examination_cell_hall_ticket_publish(scope: AccessScope) -> None:
    if Permission.EXAMINATION_CELL_HALL_TICKET_PUBLISH in scope.effective_permissions or Permission.EXAMINATION_ADMIN_PUBLISH in scope.effective_permissions:
        return
    authorize(scope, Permission.EXAMINATION_CELL_HALL_TICKET_PUBLISH)


def require_examination_cell_tenant(scope: AccessScope) -> PydanticObjectId:
    authorize_examination_cell_read(scope)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context is required", status_code=403)
    return scope.tenant_id


def require_college_tenant(scope: AccessScope) -> PydanticObjectId:
    """Tenant context without examination-cell read (e.g. assigned revaluation evaluator)."""
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context is required", status_code=403)
    return scope.tenant_id


def _has_seating_read(scope: AccessScope) -> bool:
    return (
        Permission.EXAMINATION_CELL_SEATING_READ in scope.effective_permissions
        or Permission.EXAMINATION_ADMIN_READ in scope.effective_permissions
    )


def _has_seating_manage(scope: AccessScope) -> bool:
    return (
        Permission.EXAMINATION_CELL_SEATING_MANAGE in scope.effective_permissions
        or Permission.EXAMINATION_ADMIN_CONFIG in scope.effective_permissions
    )


def authorize_examination_cell_seating_manage(scope: AccessScope) -> None:
    if _has_seating_manage(scope):
        return
    authorize(scope, Permission.EXAMINATION_CELL_SEATING_MANAGE)


def authorize_examination_cell_seating_publish(scope: AccessScope) -> None:
    if Permission.EXAMINATION_CELL_SEATING_PUBLISH in scope.effective_permissions or Permission.EXAMINATION_ADMIN_PUBLISH in scope.effective_permissions:
        return
    authorize(scope, Permission.EXAMINATION_CELL_SEATING_PUBLISH)


def _has_marks_manage(scope: AccessScope) -> bool:
    return (
        Permission.EXAMINATION_CELL_MARKS_MANAGE in scope.effective_permissions
        or Permission.EXAMINATION_ADMIN_MARKS in scope.effective_permissions
    )


def authorize_examination_cell_marks_manage(scope: AccessScope) -> None:
    if _has_marks_manage(scope):
        return
    authorize(scope, Permission.EXAMINATION_CELL_MARKS_MANAGE)


def authorize_examination_cell_marks_enter(scope: AccessScope) -> None:
    if _has_marks_manage(scope):
        return
    if Permission.EXAMINATION_CELL_MARKS_ENTER in scope.effective_permissions:
        return
    authorize(scope, Permission.EXAMINATION_CELL_MARKS_ENTER)


def authorize_examination_cell_marks_moderate(scope: AccessScope) -> None:
    if _has_marks_manage(scope):
        return
    if Permission.EXAMINATION_CELL_MARKS_MODERATE in scope.effective_permissions or Permission.EXAMINATION_ADMIN_MARKS in scope.effective_permissions:
        return
    authorize(scope, Permission.EXAMINATION_CELL_MARKS_MODERATE)


def authorize_examination_cell_grading_manage(scope: AccessScope) -> None:
    if Permission.EXAMINATION_CELL_GRADING_MANAGE in scope.effective_permissions or Permission.EXAMINATION_ADMIN_CONFIG in scope.effective_permissions:
        return
    authorize(scope, Permission.EXAMINATION_CELL_GRADING_MANAGE)


def authorize_examination_cell_result_review(scope: AccessScope) -> None:
    if Permission.EXAMINATION_CELL_RESULT_REVIEW in scope.effective_permissions or Permission.EXAMINATION_ADMIN_MARKS in scope.effective_permissions:
        return
    authorize(scope, Permission.EXAMINATION_CELL_RESULT_REVIEW)


def authorize_examination_cell_publication_manage(scope: AccessScope) -> None:
    if Permission.EXAMINATION_CELL_PUBLICATION_MANAGE in scope.effective_permissions or Permission.EXAMINATION_ADMIN_CONFIG in scope.effective_permissions:
        return
    authorize(scope, Permission.EXAMINATION_CELL_PUBLICATION_MANAGE)


def authorize_examination_cell_publication_publish(scope: AccessScope) -> None:
    if Permission.EXAMINATION_CELL_PUBLICATION_PUBLISH in scope.effective_permissions or Permission.EXAMINATION_ADMIN_PUBLISH in scope.effective_permissions:
        return
    authorize(scope, Permission.EXAMINATION_CELL_PUBLICATION_PUBLISH)


def authorize_examination_cell_document_generate(scope: AccessScope) -> None:
    if Permission.EXAMINATION_CELL_DOCUMENT_GENERATE in scope.effective_permissions or Permission.EXAMINATION_ADMIN_PUBLISH in scope.effective_permissions:
        return
    authorize(scope, Permission.EXAMINATION_CELL_DOCUMENT_GENERATE)


def authorize_examination_cell_revaluation_manage(scope: AccessScope) -> None:
    if Permission.EXAMINATION_CELL_REVALUATION_MANAGE in scope.effective_permissions or Permission.EXAMINATION_ADMIN_CONFIG in scope.effective_permissions:
        return
    authorize(scope, Permission.EXAMINATION_CELL_REVALUATION_MANAGE)


def authorize_examination_cell_supplementary_manage(scope: AccessScope) -> None:
    if Permission.EXAMINATION_CELL_SUPPLEMENTARY_MANAGE in scope.effective_permissions or Permission.EXAMINATION_ADMIN_CONFIG in scope.effective_permissions:
        return
    authorize(scope, Permission.EXAMINATION_CELL_SUPPLEMENTARY_MANAGE)


def authorize_examination_cell_incident_manage(scope: AccessScope) -> None:
    if Permission.EXAMINATION_CELL_INCIDENT_MANAGE in scope.effective_permissions or Permission.EXAMINATION_ADMIN_CONFIG in scope.effective_permissions:
        return
    authorize(scope, Permission.EXAMINATION_CELL_INCIDENT_MANAGE)


def authorize_examination_cell_notification_read(scope: AccessScope) -> None:
    if (
        Permission.EXAMINATION_CELL_NOTIFICATION_READ in scope.effective_permissions
        or Permission.EXAMINATION_CELL_NOTIFICATION_MANAGE in scope.effective_permissions
        or Permission.EXAMINATION_ADMIN_READ in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.EXAMINATION_CELL_NOTIFICATION_READ)


def authorize_examination_cell_notification_manage(scope: AccessScope) -> None:
    if Permission.EXAMINATION_CELL_NOTIFICATION_MANAGE in scope.effective_permissions or Permission.EXAMINATION_ADMIN_CONFIG in scope.effective_permissions:
        return
    authorize(scope, Permission.EXAMINATION_CELL_NOTIFICATION_MANAGE)


def authorize_examination_cell_notification_publish(scope: AccessScope) -> None:
    if (
        Permission.EXAMINATION_CELL_NOTIFICATION_PUBLISH in scope.effective_permissions
        or Permission.EXAMINATION_ADMIN_PUBLISH in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.EXAMINATION_CELL_NOTIFICATION_PUBLISH)


def authorize_examination_cell_report_read(scope: AccessScope) -> None:
    if Permission.EXAMINATION_CELL_REPORT_READ in scope.effective_permissions or Permission.EXAMINATION_ADMIN_READ in scope.effective_permissions:
        return
    authorize(scope, Permission.EXAMINATION_CELL_REPORT_READ)


def authorize_examination_cell_integration_read(scope: AccessScope) -> None:
    if (
        Permission.EXAMINATION_CELL_INTEGRATION_READ in scope.effective_permissions
        or Permission.EXAMINATION_CELL_INTEGRATION_MANAGE in scope.effective_permissions
        or Permission.EXAMINATION_ADMIN_READ in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.EXAMINATION_CELL_INTEGRATION_READ)


def authorize_examination_cell_integration_manage(scope: AccessScope) -> None:
    if Permission.EXAMINATION_CELL_INTEGRATION_MANAGE in scope.effective_permissions or Permission.EXAMINATION_ADMIN_CONFIG in scope.effective_permissions:
        return
    authorize(scope, Permission.EXAMINATION_CELL_INTEGRATION_MANAGE)


def authorize_examination_cell_audit_read(scope: AccessScope) -> None:
    if Permission.EXAMINATION_CELL_AUDIT_READ in scope.effective_permissions or Permission.EXAMINATION_ADMIN_READ in scope.effective_permissions:
        return
    authorize(scope, Permission.EXAMINATION_CELL_AUDIT_READ)


def authorize_examination_cell_security_read(scope: AccessScope) -> None:
    if (
        Permission.EXAMINATION_CELL_SECURITY_READ in scope.effective_permissions
        or Permission.EXAMINATION_CELL_SECURITY_MANAGE in scope.effective_permissions
        or Permission.EXAMINATION_ADMIN_READ in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.EXAMINATION_CELL_SECURITY_READ)


def authorize_examination_cell_security_manage(scope: AccessScope) -> None:
    if Permission.EXAMINATION_CELL_SECURITY_MANAGE in scope.effective_permissions or Permission.EXAMINATION_ADMIN_CONFIG in scope.effective_permissions:
        return
    authorize(scope, Permission.EXAMINATION_CELL_SECURITY_MANAGE)


def authorize_examination_cell_report_export(scope: AccessScope) -> None:
    if Permission.EXAMINATION_CELL_REPORT_EXPORT in scope.effective_permissions or Permission.EXAMINATION_ADMIN_PUBLISH in scope.effective_permissions:
        return
    authorize(scope, Permission.EXAMINATION_CELL_REPORT_EXPORT)


def authorize_examination_cell_incident_investigate(scope: AccessScope) -> None:
    if (
        Permission.EXAMINATION_CELL_INCIDENT_INVESTIGATE in scope.effective_permissions
        or Permission.EXAMINATION_CELL_INCIDENT_MANAGE in scope.effective_permissions
        or Permission.EXAMINATION_ADMIN_CONFIG in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.EXAMINATION_CELL_INCIDENT_INVESTIGATE)


def authorize_examination_cell_result_approve(scope: AccessScope) -> None:
    if Permission.EXAMINATION_CELL_RESULT_APPROVE in scope.effective_permissions or Permission.EXAMINATION_ADMIN_PUBLISH in scope.effective_permissions:
        return
    authorize(scope, Permission.EXAMINATION_CELL_RESULT_APPROVE)


async def resolve_department_code_filter(scope: AccessScope) -> str | None:
    """When the user is department-scoped, restrict metrics to that department code."""
    if scope.department_id is None:
        return None
    dept = await Department.get(scope.department_id)
    if dept is None or str(dept.tenant_id) != str(scope.tenant_id):
        raise AppError(code="FORBIDDEN", message="Department context is invalid", status_code=403)
    return dept.code.upper()