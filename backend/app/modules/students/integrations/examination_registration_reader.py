"""Central examination registration reads."""

from datetime import datetime, timezone

from beanie import PydanticObjectId

from app.modules.examinations.examination_registration_enums import ExaminationFeePaymentStatus
from app.modules.examinations.examination_registration_models import ExaminationFeePayment, ExaminationRegistrationWindow
from app.modules.examinations.hall_ticket_models import ExaminationHallTicket
from app.modules.examinations.examination_registration_enums import HallTicketPublicationStatus
from app.modules.examinations.semester_examination_models import SemesterExaminationSeason, StudentExaminationEligibility


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def registration_window(tenant_id: PydanticObjectId, season_id: str) -> ExaminationRegistrationWindow | None:
    return await ExaminationRegistrationWindow.find_one({"tenant_id": tenant_id, "season_id": season_id, "published": True})


async def fee_payment(
    tenant_id: PydanticObjectId, user_id: PydanticObjectId, season_id: str, fee_code: str
) -> ExaminationFeePayment | None:
    return await ExaminationFeePayment.find_one(
        {"tenant_id": tenant_id, "student_user_id": user_id, "season_id": season_id, "fee_code": fee_code}
    )


def fee_verified(payment: ExaminationFeePayment | None, *, fee_required: bool) -> bool:
    if not fee_required:
        return True
    if payment is None:
        return False
    return payment.status in {ExaminationFeePaymentStatus.PAID, ExaminationFeePaymentStatus.WAIVED}


async def published_season(tenant_id: PydanticObjectId, season_id: str) -> SemesterExaminationSeason | None:
    return await SemesterExaminationSeason.find_one({"tenant_id": tenant_id, "season_id": season_id, "published": True})


async def student_eligibility(
    tenant_id: PydanticObjectId, user_id: PydanticObjectId, season_id: str
) -> StudentExaminationEligibility | None:
    return await StudentExaminationEligibility.find_one(
        {"tenant_id": tenant_id, "student_user_id": user_id, "season_id": season_id, "published": True}
    )


async def published_hall_ticket(
    tenant_id: PydanticObjectId, user_id: PydanticObjectId, season_id: str
) -> ExaminationHallTicket | None:
    return await ExaminationHallTicket.find_one(
        {
            "tenant_id": tenant_id,
            "student_user_id": user_id,
            "season_id": season_id,
            "status": HallTicketPublicationStatus.PUBLISHED,
        }
    )


def window_open(window: ExaminationRegistrationWindow | None) -> bool:
    if window is None:
        return False
    now = _utcnow()
    return window.registration_open_at <= now <= window.registration_close_at
