"""Arrear and supplementary examination reads."""

from datetime import datetime, timezone

from beanie import PydanticObjectId

from app.modules.examinations.arrear_examination_models import (
    ArrearEligibilityRecord,
    ExaminationAttemptRecord,
    SupplementaryExaminationSeason,
)
from app.modules.examinations.examination_registration_enums import ExaminationFeePaymentStatus
from app.modules.examinations.examination_registration_models import ExaminationFeePayment
from app.modules.examinations.result_publication_models import SemesterResultSubjectMark


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def published_supplementary_seasons(tenant_id: PydanticObjectId) -> list[SupplementaryExaminationSeason]:
    return await SupplementaryExaminationSeason.find({"tenant_id": tenant_id, "published": True}).sort(
        "registration_open_at"
    ).to_list()


async def arrear_eligibility(
    tenant_id: PydanticObjectId, user_id: PydanticObjectId, supplementary_season_id: str
) -> ArrearEligibilityRecord | None:
    return await ArrearEligibilityRecord.find_one(
        {
            "tenant_id": tenant_id,
            "student_user_id": user_id,
            "supplementary_season_id": supplementary_season_id,
            "published": True,
        }
    )


async def published_attempts(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> list[ExaminationAttemptRecord]:
    return await ExaminationAttemptRecord.find(
        {"tenant_id": tenant_id, "student_user_id": user_id, "published": True}
    ).sort([("course_code", 1), ("attempt_number", 1)]).to_list()


async def pending_arrear_from_results(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> list[str]:
    rows = await SemesterResultSubjectMark.find(
        {
            "tenant_id": tenant_id,
            "student_user_id": user_id,
            "published": True,
            "pass_fail": {"$in": ["fail", "FAIL", "failed"]},
        }
    ).to_list()
    return sorted({r.course_code for r in rows})


async def supplementary_fee(
    tenant_id: PydanticObjectId, user_id: PydanticObjectId, season: SupplementaryExaminationSeason, registration_id: str
) -> ExaminationFeePayment | None:
    return await ExaminationFeePayment.find_one(
        {
            "tenant_id": tenant_id,
            "student_user_id": user_id,
            "season_id": season.supplementary_season_id,
            "fee_code": season.fee_code,
        }
    )


def fee_is_verified(payment: ExaminationFeePayment | None, *, required: bool) -> bool:
    if not required:
        return True
    if payment is None:
        return False
    return payment.status in {ExaminationFeePaymentStatus.PAID, ExaminationFeePaymentStatus.WAIVED}


def registration_window_open(season: SupplementaryExaminationSeason) -> bool:
    now = _utcnow()
    return season.registration_open_at <= now <= season.registration_close_at


async def supplementary_published_results(
    tenant_id: PydanticObjectId, user_id: PydanticObjectId, supplementary_season_id: str
) -> list[SemesterResultSubjectMark]:
    return await SemesterResultSubjectMark.find(
        {
            "tenant_id": tenant_id,
            "student_user_id": user_id,
            "season_id": supplementary_season_id,
            "is_arrear": True,
            "published": True,
        }
    ).to_list()
