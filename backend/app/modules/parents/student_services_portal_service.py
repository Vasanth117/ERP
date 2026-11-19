"""Parent view of hostel, transport, library and optional mess/welfare."""

from uuid import uuid4

from beanie import PydanticObjectId

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.parents.enums import ParentDataPermission, ParentStudentServiceType
from app.modules.parents.models import ParentStudentServiceEnquiry, ParentStudentServiceEnquiryHistory
from app.modules.parents.phase5_schemas import (
    ParentHostelSummaryRead,
    ParentLibrarySummaryRead,
    ParentMessSummaryRead,
    ParentServiceEnquiryCreate,
    ParentServiceEnquiryRead,
    ParentStudentServicesOverviewRead,
    ParentTransportSummaryRead,
)
from app.modules.parents.policy import require_parent_scope
from app.modules.parents.relationship_access import require_student_access
from app.modules.parents.student_context import resolve_student_for_parent
from app.modules.students.integrations import library_reader
from app.modules.students.integrations.residence_reader import (
    hostel_allocation,
    hostel_notices,
    hostel_requests,
    transport_allocation,
    transport_notifications,
)


async def services_overview(scope: AccessScope, parent: User, student_user_id: str) -> ParentStudentServicesOverviewRead:
    authorize(scope, Permission.PARENT_SERVICES_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_PROFILE)
    _, perms = await require_student_access(tenant_id, parent.id, sid, None)
    grants = perms.grants if perms else {}
    return ParentStudentServicesOverviewRead(
        hostel_enabled=grants.get(ParentDataPermission.VIEW_HOSTEL.value, False),
        transport_enabled=grants.get(ParentDataPermission.VIEW_TRANSPORT.value, False),
        library_enabled=grants.get(ParentDataPermission.VIEW_LIBRARY.value, False),
        mess_enabled=False,
        welfare_enabled=grants.get(ParentDataPermission.SUBMIT_SERVICE_REQUESTS.value, False),
    )


async def hostel_summary(scope: AccessScope, parent: User, student_user_id: str) -> ParentHostelSummaryRead:
    authorize(scope, Permission.PARENT_SERVICES_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_HOSTEL)
    alloc = await hostel_allocation(tenant_id, sid)
    if alloc is None:
        return ParentHostelSummaryRead(allocated=False)
    notices = await hostel_notices(tenant_id, limit=5)
    reqs = await hostel_requests(tenant_id, sid)
    return ParentHostelSummaryRead(
        allocated=True,
        hostel_name=getattr(alloc, "hostel_name", None) or getattr(alloc, "hostel_id", None),
        block=getattr(alloc, "block", None),
        room=getattr(alloc, "room_number", None),
        status="active" if alloc.published else "inactive",
        notices=[
            {"title": n.title, "body": n.body[:300], "created_at": n.created_at}
            for n in notices[:5]
        ],
    )


async def transport_summary(scope: AccessScope, parent: User, student_user_id: str) -> ParentTransportSummaryRead:
    authorize(scope, Permission.PARENT_SERVICES_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_TRANSPORT)
    alloc = await transport_allocation(tenant_id, sid)
    if alloc is None:
        return ParentTransportSummaryRead(enrolled=False)
    notifs = await transport_notifications(tenant_id, alloc.route_id)
    return ParentTransportSummaryRead(
        enrolled=True,
        route_name=alloc.route_name,
        pickup_stop=alloc.pickup_stop,
        drop_stop=alloc.drop_stop,
        notifications=[{"title": n.title, "body": n.body[:300]} for n in notifs[:5]],
    )


async def library_summary(scope: AccessScope, parent: User, student_user_id: str) -> ParentLibrarySummaryRead:
    authorize(scope, Permission.PARENT_SERVICES_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_LIBRARY)
    active = await library_reader.active_circulations(tenant_id, sid)
    reservations = await library_reader.reservations_for_student(tenant_id, sid)
    overdue = sum(1 for c in active if getattr(c, "status", None) and c.status.value == "overdue")
    return ParentLibrarySummaryRead(
        active_loans=len(active),
        overdue_loans=overdue,
        reservations=len(reservations),
        items=[
            {
                "book_id": c.book_id,
                "due_at": c.due_at,
                "status": c.status.value if c.status else None,
            }
            for c in active[:10]
        ],
    )


async def mess_summary(scope: AccessScope, parent: User, student_user_id: str) -> ParentMessSummaryRead:
    authorize(scope, Permission.PARENT_SERVICES_READ)
    require_parent_scope(scope)
    await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_PROFILE)
    return ParentMessSummaryRead(enabled=False, summary="Mess integration not enabled for this institution")


async def submit_service_enquiry(
    scope: AccessScope, parent: User, student_user_id: str, payload: ParentServiceEnquiryCreate
) -> ParentServiceEnquiryRead:
    authorize(scope, Permission.PARENT_SERVICES_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.SUBMIT_SERVICE_REQUESTS)
    rel, _ = await require_student_access(tenant_id, parent.id, sid, ParentDataPermission.SUBMIT_SERVICE_REQUESTS)
    perm = _perm_for_service(payload.service_type)
    if perm != ParentDataPermission.SUBMIT_SERVICE_REQUESTS:
        await require_student_access(tenant_id, parent.id, sid, perm)
    enquiry_id = f"pss_{uuid4().hex[:12]}"
    row = ParentStudentServiceEnquiry(
        tenant_id=tenant_id,
        enquiry_id=enquiry_id,
        parent_user_id=parent.id,
        student_user_id=sid,
        relationship_id=rel.id,
        service_type=payload.service_type.value,
        subject=payload.subject.strip(),
        description=payload.description.strip(),
    )
    await row.insert()
    await ParentStudentServiceEnquiryHistory(
        tenant_id=tenant_id,
        enquiry_id=enquiry_id,
        from_status=None,
        to_status=row.status,
        note="Submitted",
        changed_by=parent.id,
    ).insert()
    return ParentServiceEnquiryRead(
        enquiry_id=enquiry_id,
        service_type=row.service_type,
        subject=row.subject,
        status=row.status,
        created_at=row.created_at,
    )


async def list_service_enquiries(
    scope: AccessScope, parent: User, student_user_id: str
) -> list[ParentServiceEnquiryRead]:
    authorize(scope, Permission.PARENT_SERVICES_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.SUBMIT_SERVICE_REQUESTS)
    rows = await ParentStudentServiceEnquiry.find(
        {"tenant_id": tenant_id, "parent_user_id": parent.id, "student_user_id": sid}
    ).sort("-created_at").to_list()
    return [
        ParentServiceEnquiryRead(
            enquiry_id=r.enquiry_id,
            service_type=r.service_type,
            subject=r.subject,
            status=r.status,
            created_at=r.created_at,
        )
        for r in rows
    ]


def _perm_for_service(service_type: ParentStudentServiceType) -> ParentDataPermission:
    perm_map = {
        ParentStudentServiceType.HOSTEL: ParentDataPermission.VIEW_HOSTEL,
        ParentStudentServiceType.TRANSPORT: ParentDataPermission.VIEW_TRANSPORT,
        ParentStudentServiceType.LIBRARY: ParentDataPermission.VIEW_LIBRARY,
        ParentStudentServiceType.MESS: ParentDataPermission.VIEW_PROFILE,
        ParentStudentServiceType.WELFARE: ParentDataPermission.SUBMIT_SERVICE_REQUESTS,
        ParentStudentServiceType.OTHER: ParentDataPermission.SUBMIT_SERVICE_REQUESTS,
    }
    return perm_map.get(service_type, ParentDataPermission.SUBMIT_SERVICE_REQUESTS)