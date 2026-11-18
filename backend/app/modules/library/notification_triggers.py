"""Event hooks from other library services."""

from uuid import uuid4

from beanie import PydanticObjectId

from app.common.time import utcnow
from app.modules.library.library_models import LibraryCirculation, LibraryFine, LibraryReservation
from app.modules.library.notification_enums import LibraryNotificationEvent
from app.modules.library.notification_service import emit_library_notification


async def on_loan_issued(tenant_id: PydanticObjectId, circ: LibraryCirculation) -> None:
    key = f"issue:{circ.circulation_id}"
    await emit_library_notification(
        tenant_id,
        event_type=LibraryNotificationEvent.ISSUE,
        recipient_user_id=circ.student_user_id,
        dedupe_key=key,
        template_kwargs={"title": circ.title, "copy_id": circ.copy_id, "due_date": circ.due_at.isoformat()},
        branch_code=circ.branch_code,
        reference_type="circulation",
        reference_id=circ.circulation_id,
    )


async def on_reservation_ready(tenant_id: PydanticObjectId, res: LibraryReservation) -> None:
    if res.notification_sent_at:
        return
    branch_suffix = f" at branch {res.branch_code}" if res.branch_code else ""
    key = f"reservation_ready:{res.reservation_id}"
    rsv_note_id = f"nrsv_{uuid4().hex[:12]}"
    doc = await emit_library_notification(
        tenant_id,
        event_type=LibraryNotificationEvent.RESERVATION_READY,
        recipient_user_id=res.student_user_id,
        dedupe_key=key,
        template_kwargs={"title": res.title, "branch_suffix": branch_suffix},
        branch_code=res.branch_code,
        reference_type="reservation",
        reference_id=res.reservation_id,
        reservation_compat=(rsv_note_id, res.reservation_id, str(res.student_user_id)),
    )
    if doc:
        res.notification_sent_at = utcnow()
        res.updated_at = utcnow()
        await res.save()


async def on_fine_assessed(tenant_id: PydanticObjectId, fine: LibraryFine) -> None:
    key = f"fine:{fine.fine_id}"
    await emit_library_notification(
        tenant_id,
        event_type=LibraryNotificationEvent.FINE,
        recipient_user_id=fine.student_user_id,
        dedupe_key=key,
        template_kwargs={"amount": str(fine.amount), "reason": fine.reason or fine.fine_type},
        branch_code=fine.branch_code,
        reference_type="fine",
        reference_id=fine.fine_id,
    )