"""Separation of duties checks for examination workflows."""

from beanie import PydanticObjectId

from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_marks_models import ExamMarksSubmission
from app.modules.examinations.exam_cell_publication_models import ExamResultPublication
from app.modules.examinations.exam_cell_security_recorder import record_exam_security_event
from app.modules.examinations.exam_cell_security_enums import ExamSecurityEventType


async def assert_marks_approval_separation(
    tenant_id: PydanticObjectId,
    actor: User,
    submission: ExamMarksSubmission,
    *,
    request_id: str | None = None,
) -> None:
    if actor.id == submission.primary_examiner_user_id:
        await record_exam_security_event(
            tenant_id,
            event_type=ExamSecurityEventType.SEPARATION_OF_DUTIES,
            actor_id=actor.id,
            resource_type="exam_marks_submission",
            resource_id=submission.submission_id,
            detail="Marks approver cannot be primary examiner",
            request_id=request_id,
        )
        raise AppError(
            code="FORBIDDEN",
            message="Separation of duties: marks approver must differ from primary examiner",
            status_code=403,
        )


async def assert_publication_separation(
    tenant_id: PydanticObjectId,
    actor: User,
    publication: ExamResultPublication,
    *,
    request_id: str | None = None,
) -> None:
    if publication.version == 1 and publication.created_by and actor.id == publication.created_by:
        await record_exam_security_event(
            tenant_id,
            event_type=ExamSecurityEventType.SEPARATION_OF_DUTIES,
            actor_id=actor.id,
            resource_type="exam_result_publication",
            resource_id=publication.publication_id,
            detail="Publisher cannot be publication creator",
            request_id=request_id,
        )
        raise AppError(
            code="FORBIDDEN",
            message="Separation of duties: result publisher must differ from publication creator",
            status_code=403,
        )