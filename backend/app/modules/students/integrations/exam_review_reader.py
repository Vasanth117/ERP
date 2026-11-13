"""Revaluation and rechecking window and fee reads."""

from datetime import datetime, timezone

from beanie import PydanticObjectId

from app.modules.examinations.exam_review_models import ExaminationReviewFeePayment, ExaminationReviewWindow
from app.modules.examinations.examination_registration_enums import ExaminationFeePaymentStatus
from app.modules.examinations.result_publication_models import SemesterResultSubjectMark


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def review_window(tenant_id: PydanticObjectId, season_id: str, review_type: str) -> ExaminationReviewWindow | None:
    return await ExaminationReviewWindow.find_one(
        {
            "tenant_id": tenant_id,
            "season_id": season_id,
            "review_type": review_type,
            "published": True,
        }
    )


def window_open(window: ExaminationReviewWindow | None) -> bool:
    if window is None:
        return False
    now = _utcnow()
    return window.application_open_at <= now <= window.application_close_at


def withdrawal_allowed(window: ExaminationReviewWindow | None) -> bool:
    if window is None or window.withdrawal_deadline is None:
        return False
    return _utcnow() <= window.withdrawal_deadline


async def review_fee_payment(tenant_id: PydanticObjectId, request_id: str) -> ExaminationReviewFeePayment | None:
    return await ExaminationReviewFeePayment.find_one({"tenant_id": tenant_id, "request_id": request_id})


def fee_verified(payment: ExaminationReviewFeePayment | None, *, required: bool) -> bool:
    if not required:
        return True
    if payment is None:
        return False
    return payment.status in {ExaminationFeePaymentStatus.PAID, ExaminationFeePaymentStatus.WAIVED}


async def published_subject_lines(
    tenant_id: PydanticObjectId, user_id: PydanticObjectId, season_id: str
) -> list[SemesterResultSubjectMark]:
    return await SemesterResultSubjectMark.find(
        {
            "tenant_id": tenant_id,
            "student_user_id": user_id,
            "season_id": season_id,
            "published": True,
        }
    ).to_list()
