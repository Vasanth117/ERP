"""Institutional student services and request tracking."""

from uuid import uuid4

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.student_services.catalog_models import InstitutionalService
from app.modules.students.models import StudentAcademicRequest
from app.modules.students.policy import require_student_scope
from app.modules.students.student_portal_enums import StudentServiceCategory, StudentServiceRequestStatus
from app.modules.students.student_portal_models import StudentServiceRequest, StudentServiceRequestHistory
from app.modules.students.student_portal_schemas import InstitutionalServiceRead, ServiceRequestInput, ServiceRequestRead


async def list_services(scope: AccessScope, user: User) -> list[InstitutionalServiceRead]:
    authorize(scope, Permission.STUDENT_SERVICES_READ)
    tenant_id = require_student_scope(scope)
    rows = await InstitutionalService.find({"tenant_id": tenant_id, "enabled": True}).sort("title").to_list()
    return [
        InstitutionalServiceRead(
            service_id=r.service_id,
            title=r.title,
            category=r.category,
            description=r.description,
        )
        for r in rows
    ]


async def submit_service_request(scope: AccessScope, user: User, payload: ServiceRequestInput) -> ServiceRequestRead:
    authorize(scope, Permission.STUDENT_SERVICES_MANAGE)
    tenant_id = require_student_scope(scope)
    service = await InstitutionalService.find_one({"tenant_id": tenant_id, "service_id": payload.service_id, "enabled": True})
    if service is None:
        raise AppError(code="NOT_FOUND", message="Service not available", status_code=404)
    request_id = f"svr_{uuid4().hex}"
    category = StudentServiceCategory.GENERAL
    if service.category in {c.value for c in StudentServiceCategory}:
        category = StudentServiceCategory(service.category)
    row = StudentServiceRequest(
        tenant_id=tenant_id,
        user_id=user.id,
        request_id=request_id,
        service_id=service.service_id,
        category=category,
        title=payload.title.strip(),
        description=payload.description.strip(),
        status=StudentServiceRequestStatus.SUBMITTED,
    )
    await row.insert()
    await StudentServiceRequestHistory(
        tenant_id=tenant_id,
        user_id=user.id,
        request_id=request_id,
        from_status="",
        to_status=row.status.value,
    ).insert()
    await record_audit(
        actor_id=scope.user_id,
        action="student.service.request_submitted",
        resource_type="student_service_request",
        resource_id=request_id,
        tenant_id=tenant_id,
    )
    return ServiceRequestRead(
        request_id=request_id,
        category=category.value,
        title=row.title,
        status=row.status.value,
        created_at=row.created_at,
    )


async def service_request_status(scope: AccessScope, user: User, request_id: str) -> ServiceRequestRead:
    authorize(scope, Permission.STUDENT_SERVICES_READ)
    tenant_id = require_student_scope(scope)
    row = await StudentServiceRequest.find_one({"tenant_id": tenant_id, "user_id": user.id, "request_id": request_id})
    if row is None:
        raise AppError(code="NOT_FOUND", message="Request not found", status_code=404)
    return ServiceRequestRead(
        request_id=row.request_id,
        category=row.category.value,
        title=row.title,
        status=row.status.value,
        created_at=row.created_at,
    )


async def service_history(scope: AccessScope, user: User, pagination: Pagination) -> Page[ServiceRequestRead]:
    authorize(scope, Permission.STUDENT_SERVICES_READ)
    tenant_id = require_student_scope(scope)
    total = await StudentServiceRequest.find({"tenant_id": tenant_id, "user_id": user.id}).count()
    rows = (
        await StudentServiceRequest.find({"tenant_id": tenant_id, "user_id": user.id})
        .sort("-created_at")
        .skip(pagination.offset)
        .limit(pagination.limit)
        .to_list()
    )
    items = [
        ServiceRequestRead(
            request_id=r.request_id,
            category=r.category.value,
            title=r.title,
            status=r.status.value,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def academic_service_requests(scope: AccessScope, user: User, pagination: Pagination) -> Page[dict]:
    authorize(scope, Permission.STUDENT_SERVICES_READ)
    tenant_id = require_student_scope(scope)
    total = await StudentAcademicRequest.find({"tenant_id": tenant_id, "user_id": user.id}).count()
    rows = (
        await StudentAcademicRequest.find({"tenant_id": tenant_id, "user_id": user.id})
        .sort("-submitted_at")
        .skip(pagination.offset)
        .limit(pagination.limit)
        .to_list()
    )
    items = [
        {
            "request_id": str(r.id),
            "request_type": r.request_type.value,
            "title": r.title,
            "status": r.status.value,
            "submitted_at": r.submitted_at,
        }
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)
