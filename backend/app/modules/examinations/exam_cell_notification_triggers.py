"""Event hooks for examination notifications (call from domain services)."""

from beanie import PydanticObjectId

from app.modules.examinations.exam_cell_notification_enums import ExamNotificationEvent
from app.modules.examinations.exam_cell_notification_service import emit_exam_notification


async def notify_registration_confirmed(
    tenant_id: PydanticObjectId,
    *,
    student_user_id: PydanticObjectId,
    exam_session_id: PydanticObjectId,
    session_name: str,
    registration_id: str,
    subject_count: int,
) -> None:
    await emit_exam_notification(
        tenant_id,
        event_type=ExamNotificationEvent.REGISTRATION_CONFIRMED,
        recipient_user_id=student_user_id,
        dedupe_key=f"reg_confirm:{registration_id}",
        template_kwargs={
            "session_name": session_name,
            "subject_count": str(subject_count),
        },
        exam_session_id=exam_session_id,
        reference_type="exam_registration",
        reference_id=registration_id,
    )


async def notify_result_published(
    tenant_id: PydanticObjectId,
    *,
    student_user_id: PydanticObjectId,
    exam_session_id: PydanticObjectId,
    session_name: str,
    publication_id: str,
) -> None:
    await emit_exam_notification(
        tenant_id,
        event_type=ExamNotificationEvent.RESULT_PUBLISHED,
        recipient_user_id=student_user_id,
        dedupe_key=f"result_pub:{publication_id}:{student_user_id}",
        template_kwargs={"session_name": session_name},
        exam_session_id=exam_session_id,
        reference_type="exam_publication",
        reference_id=publication_id,
    )


async def notify_hall_ticket_available(
    tenant_id: PydanticObjectId,
    *,
    student_user_id: PydanticObjectId,
    exam_session_id: PydanticObjectId,
    session_name: str,
    hall_ticket_id: str,
) -> None:
    await emit_exam_notification(
        tenant_id,
        event_type=ExamNotificationEvent.HALL_TICKET_AVAILABLE,
        recipient_user_id=student_user_id,
        dedupe_key=f"hall_ticket:{hall_ticket_id}",
        template_kwargs={"session_name": session_name},
        exam_session_id=exam_session_id,
        reference_type="exam_hall_ticket",
        reference_id=hall_ticket_id,
    )


async def notify_eligibility_published(
    tenant_id: PydanticObjectId,
    *,
    student_user_id: PydanticObjectId,
    exam_session_id: PydanticObjectId,
    session_name: str,
    eligibility_id: str,
) -> None:
    await emit_exam_notification(
        tenant_id,
        event_type=ExamNotificationEvent.ELIGIBILITY_PUBLISHED,
        recipient_user_id=student_user_id,
        dedupe_key=f"eligibility:{eligibility_id}",
        template_kwargs={"session_name": session_name},
        exam_session_id=exam_session_id,
        reference_type="exam_eligibility",
        reference_id=eligibility_id,
    )


async def notify_revaluation_update(
    tenant_id: PydanticObjectId,
    *,
    student_user_id: PydanticObjectId,
    application_id: str,
    status_message: str,
    exam_session_id: PydanticObjectId | None = None,
) -> None:
    await emit_exam_notification(
        tenant_id,
        event_type=ExamNotificationEvent.REVALUATION_UPDATE,
        recipient_user_id=student_user_id,
        dedupe_key=f"reval_update:{application_id}:{status_message[:32]}",
        template_kwargs={"status_message": status_message},
        exam_session_id=exam_session_id,
        reference_type="exam_revaluation_application",
        reference_id=application_id,
    )


async def notify_incident_workflow(
    tenant_id: PydanticObjectId,
    *,
    recipient_user_id: PydanticObjectId,
    case_id: str,
    summary: str,
    exam_session_id: PydanticObjectId | None = None,
) -> None:
    await emit_exam_notification(
        tenant_id,
        event_type=ExamNotificationEvent.INCIDENT_WORKFLOW,
        recipient_user_id=recipient_user_id,
        dedupe_key=f"incident:{case_id}:{recipient_user_id}:{summary[:40]}",
        template_kwargs={"summary": summary},
        exam_session_id=exam_session_id,
        reference_type="exam_malpractice_case",
        reference_id=case_id,
        restricted=True,
    )