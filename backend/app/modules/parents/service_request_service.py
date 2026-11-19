"""Parent student-service requests."""

from uuid import uuid4

from beanie import PydanticObjectId

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.parents.enums import (
    PARENT_SERVICE_REQUEST_TYPES,
    ParentDataPermission,
    ParentServiceRequestCategory,
    ParentServiceRequestStatus,
)
from app.modules.parents.models import ParentServiceRequestComment, ParentServiceRequestHistory, ParentStudentServiceRequest
from app.modules.parents.phase4_schemas import (
    ParentServiceRequestCommentCreate,
    ParentServiceRequestCommentRead,
    ParentServiceRequestCreate,
    ParentServiceRequestRead,
    ParentServiceRequestTypesRead,
)
from app.modules.parents.policy import require_parent_scope
from app.modules.parents.relationship_access import require_student_access
from app.modules.parents.student_context import resolve_student_for_parent

_VALID_PRIORITIES = frozenset({"low", "normal", "high", "urgent"})

_TEAM_BY_CATEGORY = {
    ParentServiceRequestCategory.ACADEMIC.value: "academic_office",
    ParentServiceRequestCategory.ADMINISTRATIVE.value: "administration",
    ParentServiceRequestCategory.FINANCIAL.value: "finance",
    ParentServiceRequestCategory.STUDENT_SERVICE.value: "student_services",
    ParentServiceRequestCategory.OTHER.value: "general",
}


async def list_request_types(scope: AccessScope, category: ParentServiceRequestCategory) -> ParentServiceRequestTypesRead:
    from app.authorization.policy import authorize
    from app.authorization.permissions import Permission

    authorize(scope, Permission.PARENT_SERVICE_REQUEST_SUBMIT)
    return ParentServiceRequestTypesRead(
        category=category,
        request_types=PARENT_SERVICE_REQUEST_TYPES.get(category.value, ["general"]),
    )


async def create_service_request(
    scope: AccessScope, parent: User, student_user_id: str, payload: ParentServiceRequestCreate
) -> ParentServiceRequestRead:
    authorize(scope, Permission.PARENT_SERVICE_REQUEST_SUBMIT)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.SUBMIT_SERVICE_REQUESTS)
    rel, _ = await require_student_access(tenant_id, parent.id, sid, ParentDataPermission.SUBMIT_SERVICE_REQUESTS)
    allowed = PARENT_SERVICE_REQUEST_TYPES.get(payload.category.value, [])
    if payload.request_type not in allowed:
        raise AppError(code="VALIDATION_ERROR", message="Request type not allowed for category", status_code=422)
    if payload.priority not in _VALID_PRIORITIES:
        raise AppError(code="VALIDATION_ERROR", message="Invalid priority", status_code=422)

    request_id = f"psr_{uuid4().hex[:12]}"
    team = _TEAM_BY_CATEGORY.get(payload.category.value, "general")
    row = ParentStudentServiceRequest(
        tenant_id=tenant_id,
        request_id=request_id,
        parent_user_id=parent.id,
        student_user_id=sid,
        relationship_id=rel.id,
        category=payload.category.value,
        request_type=payload.request_type,
        subject=payload.subject.strip(),
        description=payload.description.strip(),
        priority=payload.priority,
        status=ParentServiceRequestStatus.SUBMITTED.value,
        assigned_team=team,
        supporting_document_refs=list(payload.supporting_document_refs),
    )
    await row.insert()
    await ParentServiceRequestHistory(
        tenant_id=tenant_id,
        service_request_id=row.id,
        request_id=request_id,
        from_status=None,
        to_status=row.status,
        note="Submitted by parent",
        changed_by=parent.id,
    ).insert()
    return _to_read(row)


async def list_service_requests(scope: AccessScope, parent: User, student_user_id: str) -> list[ParentServiceRequestRead]:
    authorize(scope, Permission.PARENT_SERVICE_REQUEST_SUBMIT)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.SUBMIT_SERVICE_REQUESTS)
    rows = await ParentStudentServiceRequest.find(
        {"tenant_id": tenant_id, "parent_user_id": parent.id, "student_user_id": sid}
    ).sort("-created_at").to_list()
    return [_to_read(r) for r in rows]


async def get_service_request(
    scope: AccessScope, parent: User, student_user_id: str, request_id: str
) -> ParentServiceRequestRead:
    authorize(scope, Permission.PARENT_SERVICE_REQUEST_SUBMIT)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.SUBMIT_SERVICE_REQUESTS)
    row = await ParentStudentServiceRequest.find_one(
        {"tenant_id": tenant_id, "parent_user_id": parent.id, "student_user_id": sid, "request_id": request_id}
    )
    if row is None:
        raise AppError(code="NOT_FOUND", message="Service request not found", status_code=404)
    return _to_read(row)


async def add_service_request_comment(
    scope: AccessScope,
    parent: User,
    student_user_id: str,
    request_id: str,
    payload: ParentServiceRequestCommentCreate,
) -> ParentServiceRequestCommentRead:
    authorize(scope, Permission.PARENT_SERVICE_REQUEST_SUBMIT)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.SUBMIT_SERVICE_REQUESTS)
    row = await ParentStudentServiceRequest.find_one(
        {"tenant_id": tenant_id, "parent_user_id": parent.id, "student_user_id": sid, "request_id": request_id}
    )
    if row is None:
        raise AppError(code="NOT_FOUND", message="Service request not found", status_code=404)
    if row.status in {ParentServiceRequestStatus.CLOSED.value, ParentServiceRequestStatus.CANCELLED.value}:
        raise AppError(code="CONFLICT", message="Request is closed", status_code=409)
    comment = ParentServiceRequestComment(
        tenant_id=tenant_id,
        service_request_id=row.id,
        request_id=request_id,
        author_user_id=parent.id,
        author_role="parent",
        body=payload.body.strip(),
        attachment_refs=list(payload.attachment_refs),
    )
    await comment.insert()
    if row.status == ParentServiceRequestStatus.AWAITING_INFORMATION.value:
        prev = row.status
        row.status = ParentServiceRequestStatus.UNDER_REVIEW.value
        row.updated_at = utcnow()
        await row.save()
        await ParentServiceRequestHistory(
            tenant_id=tenant_id,
            service_request_id=row.id,
            request_id=request_id,
            from_status=prev,
            to_status=row.status,
            note="Parent provided additional information",
            changed_by=parent.id,
        ).insert()
    return ParentServiceRequestCommentRead(
        comment_id=str(comment.id),
        author_role=comment.author_role,
        body=comment.body,
        created_at=comment.created_at,
    )


async def list_service_request_comments(
    scope: AccessScope, parent: User, student_user_id: str, request_id: str
) -> list[ParentServiceRequestCommentRead]:
    authorize(scope, Permission.PARENT_SERVICE_REQUEST_SUBMIT)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.SUBMIT_SERVICE_REQUESTS)
    row = await ParentStudentServiceRequest.find_one(
        {"tenant_id": tenant_id, "parent_user_id": parent.id, "student_user_id": sid, "request_id": request_id}
    )
    if row is None:
        raise AppError(code="NOT_FOUND", message="Service request not found", status_code=404)
    comments = await ParentServiceRequestComment.find(
        {"tenant_id": tenant_id, "service_request_id": row.id}
    ).sort("created_at").to_list()
    return [
        ParentServiceRequestCommentRead(
            comment_id=str(c.id),
            author_role=c.author_role,
            body=c.body,
            created_at=c.created_at,
        )
        for c in comments
    ]


def _to_read(row: ParentStudentServiceRequest) -> ParentServiceRequestRead:
    return ParentServiceRequestRead(
        request_id=row.request_id,
        category=row.category,
        request_type=row.request_type,
        subject=row.subject,
        description=row.description,
        status=row.status,
        priority=row.priority,
        assigned_team=row.assigned_team,
        resolution_remarks=row.resolution_remarks,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )