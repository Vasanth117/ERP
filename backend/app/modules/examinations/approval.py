"""Marks approval workflow (examination cell / admin)."""

from beanie import PydanticObjectId

from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.examinations.enums import MarksBatchStatus, StudentMarkStatus
from app.modules.examinations.models import MarksApprovalHistory, MarksSubmissionBatch, StudentAssessmentMark


async def approve_marks_batch(tenant_id: PydanticObjectId, batch_id: PydanticObjectId, *, actor_id: PydanticObjectId) -> None:
    batch = await MarksSubmissionBatch.get(batch_id)
    if batch is None or str(batch.tenant_id) != str(tenant_id):
        raise AppError(code="NOT_FOUND", message="Marks batch not found", status_code=404)
    if batch.status not in {MarksBatchStatus.SUBMITTED, MarksBatchStatus.PENDING_APPROVAL}:
        raise AppError(code="CONFLICT", message="Batch is not awaiting approval", status_code=409)
    batch.status = MarksBatchStatus.APPROVED
    batch.approved_at = utcnow()
    batch.updated_at = utcnow()
    await batch.save()
    marks = await StudentAssessmentMark.find({"batch_id": batch_id}).to_list()
    for mark in marks:
        mark.status = StudentMarkStatus.APPROVED
        await mark.save()
    await MarksApprovalHistory(
        tenant_id=tenant_id,
        batch_id=batch_id,
        action="approved",
        actor_id=actor_id,
        note="Marks approved",
    ).insert()
