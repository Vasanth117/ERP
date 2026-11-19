"""College admin responses to parent academic and attendance enquiries."""

from beanie import PydanticObjectId

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.parents.models import (
    ParentAcademicEnquiry,
    ParentAttendanceEnquiry,
    ParentAttendanceEnquiryHistory,
    ParentDocumentAccessRequest,
    ParentFinanceEnquiry,
    ParentFinanceEnquiryHistory,
    ParentRelationshipAccessReviewRequest,
    ParentStudentServiceEnquiry,
    ParentStudentServiceEnquiryHistory,
)
from app.modules.parents.phase2_schemas import ParentEnquiryReview


async def list_attendance_enquiries_admin(scope: AccessScope, *, status: str | None = None) -> list[dict]:
    authorize(scope, Permission.PARENT_ADMIN_READ)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context required", status_code=403)
    filters: dict = {"tenant_id": scope.tenant_id}
    if status:
        filters["status"] = status
    rows = await ParentAttendanceEnquiry.find(filters).sort("-created_at").limit(200).to_list()
    return [
        {
            "enquiry_id": str(r.id),
            "student_user_id": str(r.student_user_id),
            "parent_user_id": str(r.parent_user_id),
            "category": r.category,
            "status": r.status,
            "created_at": r.created_at,
        }
        for r in rows
    ]


async def respond_attendance_enquiry(
    scope: AccessScope,
    enquiry_id: PydanticObjectId,
    payload: ParentEnquiryReview,
    *,
    reviewer_id: PydanticObjectId,
) -> dict:
    authorize(scope, Permission.PARENT_ADMIN_MANAGE)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context required", status_code=403)
    doc = await ParentAttendanceEnquiry.get(enquiry_id)
    if doc is None or str(doc.tenant_id) != str(scope.tenant_id):
        raise AppError(code="NOT_FOUND", message="Enquiry not found", status_code=404)
    prev = doc.status
    if payload.status:
        doc.status = payload.status
    else:
        doc.status = "responded"
    if payload.assigned_team:
        doc.assigned_team = payload.assigned_team
    doc.response_notes = payload.response_notes
    doc.responded_by = reviewer_id
    doc.responded_at = utcnow()
    doc.updated_at = utcnow()
    await doc.save()
    await ParentAttendanceEnquiryHistory(
        tenant_id=doc.tenant_id,
        enquiry_id=doc.id,
        from_status=prev,
        to_status=doc.status,
        note=payload.response_notes,
        changed_by=reviewer_id,
    ).insert()
    return {"enquiry_id": str(doc.id), "status": doc.status}


async def list_document_access_requests_admin(scope: AccessScope, *, status: str | None = None) -> list[dict]:
    authorize(scope, Permission.PARENT_ADMIN_READ)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context required", status_code=403)
    filters: dict = {"tenant_id": scope.tenant_id}
    if status:
        filters["status"] = status
    rows = await ParentDocumentAccessRequest.find(filters).sort("-created_at").limit(200).to_list()
    return [
        {
            "request_id": str(r.id),
            "parent_user_id": str(r.parent_user_id),
            "student_user_id": str(r.student_user_id),
            "document_type": r.document_type,
            "status": r.status,
            "created_at": r.created_at,
        }
        for r in rows
    ]


async def respond_document_access_request(
    scope: AccessScope,
    request_id: PydanticObjectId,
    payload: ParentEnquiryReview,
    *,
    reviewer_id: PydanticObjectId,
) -> dict:
    authorize(scope, Permission.PARENT_ADMIN_MANAGE)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context required", status_code=403)
    doc = await ParentDocumentAccessRequest.get(request_id)
    if doc is None or str(doc.tenant_id) != str(scope.tenant_id):
        raise AppError(code="NOT_FOUND", message="Document request not found", status_code=404)
    doc.status = payload.status or "responded"
    doc.response_notes = payload.response_notes
    doc.updated_at = utcnow()
    await doc.save()
    return {"request_id": str(doc.id), "status": doc.status}


async def list_student_service_enquiries_admin(scope: AccessScope, *, status: str | None = None) -> list[dict]:
    authorize(scope, Permission.PARENT_ADMIN_READ)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context required", status_code=403)
    filters: dict = {"tenant_id": scope.tenant_id}
    if status:
        filters["status"] = status
    rows = await ParentStudentServiceEnquiry.find(filters).sort("-created_at").limit(200).to_list()
    return [
        {
            "enquiry_id": r.enquiry_id,
            "student_user_id": str(r.student_user_id),
            "parent_user_id": str(r.parent_user_id),
            "service_type": r.service_type,
            "status": r.status,
            "created_at": r.created_at,
        }
        for r in rows
    ]


async def respond_student_service_enquiry(
    scope: AccessScope,
    enquiry_id: str,
    payload: ParentEnquiryReview,
    *,
    reviewer_id: PydanticObjectId,
) -> dict:
    authorize(scope, Permission.PARENT_ADMIN_MANAGE)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context required", status_code=403)
    doc = await ParentStudentServiceEnquiry.find_one({"tenant_id": scope.tenant_id, "enquiry_id": enquiry_id})
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Service enquiry not found", status_code=404)
    prev = doc.status
    doc.status = payload.status or "responded"
    doc.response_notes = payload.response_notes
    doc.updated_at = utcnow()
    await doc.save()
    await ParentStudentServiceEnquiryHistory(
        tenant_id=doc.tenant_id,
        enquiry_id=enquiry_id,
        from_status=prev,
        to_status=doc.status,
        note=payload.response_notes,
        changed_by=reviewer_id,
    ).insert()
    return {"enquiry_id": enquiry_id, "status": doc.status}


async def list_relationship_review_requests_admin(scope: AccessScope, *, status: str | None = None) -> list[dict]:
    authorize(scope, Permission.PARENT_ADMIN_READ)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context required", status_code=403)
    filters: dict = {"tenant_id": scope.tenant_id}
    if status:
        filters["status"] = status
    rows = await ParentRelationshipAccessReviewRequest.find(filters).sort("-created_at").limit(200).to_list()
    return [
        {
            "request_id": str(r.id),
            "parent_user_id": str(r.parent_user_id),
            "student_user_id": str(r.student_user_id),
            "action": r.action,
            "status": r.status,
            "created_at": r.created_at,
        }
        for r in rows
    ]


async def respond_relationship_review_request(
    scope: AccessScope,
    request_id: PydanticObjectId,
    payload: ParentEnquiryReview,
    *,
    reviewer_id: PydanticObjectId,
) -> dict:
    authorize(scope, Permission.PARENT_ADMIN_MANAGE)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context required", status_code=403)
    doc = await ParentRelationshipAccessReviewRequest.get(request_id)
    if doc is None or str(doc.tenant_id) != str(scope.tenant_id):
        raise AppError(code="NOT_FOUND", message="Review request not found", status_code=404)
    doc.status = payload.status or "responded"
    doc.updated_at = utcnow()
    await doc.save()
    return {"request_id": str(doc.id), "status": doc.status}


async def list_academic_enquiries_admin(scope: AccessScope, *, status: str | None = None) -> list[dict]:
    authorize(scope, Permission.PARENT_ADMIN_READ)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context required", status_code=403)
    filters: dict = {"tenant_id": scope.tenant_id}
    if status:
        filters["status"] = status
    rows = await ParentAcademicEnquiry.find(filters).sort("-created_at").limit(200).to_list()
    return [
        {
            "enquiry_id": str(r.id),
            "student_user_id": str(r.student_user_id),
            "parent_user_id": str(r.parent_user_id),
            "category": r.category,
            "status": r.status,
            "created_at": r.created_at,
        }
        for r in rows
    ]


async def respond_academic_enquiry(
    scope: AccessScope,
    enquiry_id: PydanticObjectId,
    payload: ParentEnquiryReview,
    *,
    reviewer_id: PydanticObjectId,
) -> dict:
    authorize(scope, Permission.PARENT_ADMIN_MANAGE)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context required", status_code=403)
    doc = await ParentAcademicEnquiry.get(enquiry_id)
    if doc is None or str(doc.tenant_id) != str(scope.tenant_id):
        raise AppError(code="NOT_FOUND", message="Enquiry not found", status_code=404)
    doc.status = payload.status or "responded"
    doc.response_notes = payload.response_notes
    doc.responded_by = reviewer_id
    doc.responded_at = utcnow()
    doc.updated_at = utcnow()
    await doc.save()
    return {"enquiry_id": str(doc.id), "status": doc.status}


async def list_finance_enquiries_admin(scope: AccessScope, *, status: str | None = None) -> list[dict]:
    authorize(scope, Permission.PARENT_ADMIN_READ)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context required", status_code=403)
    filters: dict = {"tenant_id": scope.tenant_id}
    if status:
        filters["status"] = status
    rows = await ParentFinanceEnquiry.find(filters).sort("-created_at").limit(200).to_list()
    return [
        {
            "enquiry_id": str(r.id),
            "student_user_id": str(r.student_user_id),
            "parent_user_id": str(r.parent_user_id),
            "category": r.category,
            "status": r.status,
            "created_at": r.created_at,
        }
        for r in rows
    ]


async def respond_finance_enquiry(
    scope: AccessScope,
    enquiry_id: PydanticObjectId,
    payload: ParentEnquiryReview,
    *,
    reviewer_id: PydanticObjectId,
) -> dict:
    authorize(scope, Permission.PARENT_ADMIN_MANAGE)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context required", status_code=403)
    doc = await ParentFinanceEnquiry.get(enquiry_id)
    if doc is None or str(doc.tenant_id) != str(scope.tenant_id):
        raise AppError(code="NOT_FOUND", message="Enquiry not found", status_code=404)
    prev = doc.status
    doc.status = payload.status or "responded"
    doc.response_notes = payload.response_notes
    doc.responded_by = reviewer_id
    doc.responded_at = utcnow()
    doc.updated_at = utcnow()
    await doc.save()
    await ParentFinanceEnquiryHistory(
        tenant_id=doc.tenant_id,
        enquiry_id=doc.id,
        from_status=prev,
        to_status=doc.status,
        note=payload.response_notes,
        changed_by=reviewer_id,
    ).insert()
    return {"enquiry_id": str(doc.id), "status": doc.status}


async def list_document_access_requests_admin(scope: AccessScope, *, status: str | None = None) -> list[dict]:
    authorize(scope, Permission.PARENT_ADMIN_READ)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context required", status_code=403)
    filters: dict = {"tenant_id": scope.tenant_id}
    if status:
        filters["status"] = status
    rows = await ParentDocumentAccessRequest.find(filters).sort("-created_at").limit(200).to_list()
    return [
        {
            "request_id": str(r.id),
            "parent_user_id": str(r.parent_user_id),
            "student_user_id": str(r.student_user_id),
            "document_type": r.document_type,
            "status": r.status,
            "created_at": r.created_at,
        }
        for r in rows
    ]


async def respond_document_access_request(
    scope: AccessScope,
    request_id: PydanticObjectId,
    payload: ParentEnquiryReview,
    *,
    reviewer_id: PydanticObjectId,
) -> dict:
    authorize(scope, Permission.PARENT_ADMIN_MANAGE)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context required", status_code=403)
    doc = await ParentDocumentAccessRequest.get(request_id)
    if doc is None or str(doc.tenant_id) != str(scope.tenant_id):
        raise AppError(code="NOT_FOUND", message="Document request not found", status_code=404)
    doc.status = payload.status or "responded"
    doc.response_notes = payload.response_notes
    doc.updated_at = utcnow()
    await doc.save()
    return {"request_id": str(doc.id), "status": doc.status}


async def list_student_service_enquiries_admin(scope: AccessScope, *, status: str | None = None) -> list[dict]:
    authorize(scope, Permission.PARENT_ADMIN_READ)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context required", status_code=403)
    filters: dict = {"tenant_id": scope.tenant_id}
    if status:
        filters["status"] = status
    rows = await ParentStudentServiceEnquiry.find(filters).sort("-created_at").limit(200).to_list()
    return [
        {
            "enquiry_id": r.enquiry_id,
            "student_user_id": str(r.student_user_id),
            "parent_user_id": str(r.parent_user_id),
            "service_type": r.service_type,
            "status": r.status,
            "created_at": r.created_at,
        }
        for r in rows
    ]


async def respond_student_service_enquiry(
    scope: AccessScope,
    enquiry_id: str,
    payload: ParentEnquiryReview,
    *,
    reviewer_id: PydanticObjectId,
) -> dict:
    authorize(scope, Permission.PARENT_ADMIN_MANAGE)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context required", status_code=403)
    doc = await ParentStudentServiceEnquiry.find_one({"tenant_id": scope.tenant_id, "enquiry_id": enquiry_id})
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Service enquiry not found", status_code=404)
    prev = doc.status
    doc.status = payload.status or "responded"
    doc.response_notes = payload.response_notes
    doc.updated_at = utcnow()
    await doc.save()
    await ParentStudentServiceEnquiryHistory(
        tenant_id=doc.tenant_id,
        enquiry_id=enquiry_id,
        from_status=prev,
        to_status=doc.status,
        note=payload.response_notes,
        changed_by=reviewer_id,
    ).insert()
    return {"enquiry_id": enquiry_id, "status": doc.status}


async def list_relationship_review_requests_admin(scope: AccessScope, *, status: str | None = None) -> list[dict]:
    authorize(scope, Permission.PARENT_ADMIN_READ)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context required", status_code=403)
    filters: dict = {"tenant_id": scope.tenant_id}
    if status:
        filters["status"] = status
    rows = await ParentRelationshipAccessReviewRequest.find(filters).sort("-created_at").limit(200).to_list()
    return [
        {
            "request_id": str(r.id),
            "parent_user_id": str(r.parent_user_id),
            "student_user_id": str(r.student_user_id),
            "action": r.action,
            "status": r.status,
            "created_at": r.created_at,
        }
        for r in rows
    ]


async def respond_relationship_review_request(
    scope: AccessScope,
    request_id: PydanticObjectId,
    payload: ParentEnquiryReview,
    *,
    reviewer_id: PydanticObjectId,
) -> dict:
    authorize(scope, Permission.PARENT_ADMIN_MANAGE)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context required", status_code=403)
    doc = await ParentRelationshipAccessReviewRequest.get(request_id)
    if doc is None or str(doc.tenant_id) != str(scope.tenant_id):
        raise AppError(code="NOT_FOUND", message="Review request not found", status_code=404)
    doc.status = payload.status or "responded"
    doc.updated_at = utcnow()
    await doc.save()
    return {"request_id": str(doc.id), "status": doc.status}