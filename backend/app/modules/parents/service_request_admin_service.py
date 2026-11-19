"""College admin workflow for parent student-service requests."""

from beanie import PydanticObjectId

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.parents.models import (
    ParentServiceRequestAssignment,
    ParentServiceRequestComment,
    ParentServiceRequestHistory,
    ParentStudentServiceRequest,
)
from app.modules.parents.phase4_schemas import ParentServiceRequestAdminUpdate


async def list_service_requests_admin(scope: AccessScope, *, status: str | None = None) -> list[dict]:
    authorize(scope, Permission.PARENT_ADMIN_READ)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context required", status_code=403)
    filters: dict = {"tenant_id": scope.tenant_id}
    if status:
        filters["status"] = status
    rows = await ParentStudentServiceRequest.find(filters).sort("-created_at").limit(200).to_list()
    return [
        {
            "request_id": r.request_id,
            "student_user_id": str(r.student_user_id),
            "parent_user_id": str(r.parent_user_id),
            "category": r.category,
            "request_type": r.request_type,
            "subject": r.subject,
            "status": r.status,
            "assigned_team": r.assigned_team,
            "created_at": r.created_at,
        }
        for r in rows
    ]


async def update_service_request_admin(
    scope: AccessScope,
    request_id: str,
    payload: ParentServiceRequestAdminUpdate,
    *,
    reviewer_id: PydanticObjectId,
) -> dict:
    authorize(scope, Permission.PARENT_ADMIN_MANAGE)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context required", status_code=403)
    row = await ParentStudentServiceRequest.find_one({"tenant_id": scope.tenant_id, "request_id": request_id})
    if row is None:
        raise AppError(code="NOT_FOUND", message="Service request not found", status_code=404)
    prev = row.status
    if payload.status:
        row.status = payload.status
    if payload.assigned_team:
        row.assigned_team = payload.assigned_team
        await ParentServiceRequestAssignment(
            tenant_id=row.tenant_id,
            request_id=request_id,
            service_request_id=row.id,
            assigned_team=payload.assigned_team,
            assigned_by=reviewer_id,
        ).insert()
    if payload.resolution_remarks:
        row.resolution_remarks = payload.resolution_remarks
    row.updated_at = utcnow()
    await row.save()
    await ParentServiceRequestHistory(
        tenant_id=row.tenant_id,
        service_request_id=row.id,
        request_id=request_id,
        from_status=prev,
        to_status=row.status,
        note=payload.resolution_remarks or payload.staff_response,
        changed_by=reviewer_id,
    ).insert()
    if payload.staff_response:
        await ParentServiceRequestComment(
            tenant_id=row.tenant_id,
            service_request_id=row.id,
            request_id=request_id,
            author_user_id=reviewer_id,
            author_role="staff",
            body=payload.staff_response.strip(),
        ).insert()
    return {"request_id": request_id, "status": row.status}