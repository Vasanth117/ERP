"""General parent support enquiries routed to institution helpdesk when configured."""

from uuid import uuid4

from beanie import PydanticObjectId

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.helpdesk_admin_models import (
    InstitutionSupportTicket,
    RequesterAudience,
    SupportPriority,
    SupportTicketStatus,
)
from app.modules.parents.enums import ParentSupportEnquiryCategory, ParentSupportEnquiryStatus
from app.modules.parents.models import ParentSupportEnquiry
from app.modules.parents.phase4_schemas import ParentSupportEnquiryCreate, ParentSupportEnquiryRead
from app.modules.parents.policy import require_parent_scope

_CATEGORY_TO_HELPDESK = {
    ParentSupportEnquiryCategory.ACCOUNT.value: ("parent_portal", "account"),
    ParentSupportEnquiryCategory.LINKING.value: ("parent_portal", "linking"),
    ParentSupportEnquiryCategory.DOCUMENT_ACCESS.value: ("parent_portal", "documents"),
    ParentSupportEnquiryCategory.TECHNICAL.value: ("platform", "access"),
    ParentSupportEnquiryCategory.GENERAL.value: ("parent_portal", "general"),
}


async def submit_support_enquiry(scope: AccessScope, parent: User, payload: ParentSupportEnquiryCreate) -> ParentSupportEnquiryRead:
    authorize(scope, Permission.PARENT_SUPPORT_SUBMIT)
    tenant_id = require_parent_scope(scope)
    enquiry_id = f"pse_{uuid4().hex[:12]}"
    module_key, issue_type = _CATEGORY_TO_HELPDESK.get(payload.category, ("parent_portal", "general"))
    ticket_id = f"ticket_{uuid4().hex[:12]}"
    ticket_number = f"PARENT-{enquiry_id[-6:].upper()}"
    ticket = InstitutionSupportTicket(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        ticket_number=ticket_number,
        title=payload.subject.strip()[:200],
        description=payload.description.strip(),
        category_code=payload.category[:64],
        module_key=module_key,
        issue_type=issue_type,
        priority=SupportPriority.NORMAL,
        requester_user_id=parent.id,
        requester_audience=RequesterAudience.PARENT,
        status=SupportTicketStatus.OPEN,
    )
    await ticket.insert()
    row = ParentSupportEnquiry(
        tenant_id=tenant_id,
        enquiry_id=enquiry_id,
        parent_user_id=parent.id,
        category=payload.category,
        subject=payload.subject.strip(),
        description=payload.description.strip(),
        status=ParentSupportEnquiryStatus.ROUTED.value,
        helpdesk_ticket_id=ticket_id,
    )
    await row.insert()
    return _to_read(row)


async def list_support_enquiries(scope: AccessScope, parent: User) -> list[ParentSupportEnquiryRead]:
    authorize(scope, Permission.PARENT_SUPPORT_SUBMIT)
    tenant_id = require_parent_scope(scope)
    rows = await ParentSupportEnquiry.find({"tenant_id": tenant_id, "parent_user_id": parent.id}).sort("-created_at").to_list()
    return [_to_read(r) for r in rows]


def _to_read(row: ParentSupportEnquiry) -> ParentSupportEnquiryRead:
    return ParentSupportEnquiryRead(
        enquiry_id=row.enquiry_id,
        category=row.category,
        subject=row.subject,
        status=row.status,
        description=row.description,
        helpdesk_ticket_id=row.helpdesk_ticket_id,
        response_notes=row.response_notes,
        created_at=row.created_at,
    )