"""Central revaluation and rechecking windows (examination cell)."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel

from app.common.time import utcnow
from app.modules.examinations.examination_registration_enums import ExaminationFeePaymentStatus


class ExaminationReviewWindow(Document):
    tenant_id: PydanticObjectId
    season_id: str
    review_type: str
    application_open_at: datetime
    application_close_at: datetime
    withdrawal_deadline: datetime | None = None
    fee_required: bool = True
    fee_amount: float = Field(default=0, ge=0)
    fee_code: str
    published: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "examination_review_windows"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("season_id", ASCENDING), ("review_type", ASCENDING)],
                unique=True,
                name="unique_review_window",
            ),
        ]


class ExaminationReviewFeePayment(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    request_id: str
    fee_code: str
    amount: float = Field(ge=0)
    status: ExaminationFeePaymentStatus = ExaminationFeePaymentStatus.PENDING
    verified_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "examination_review_fee_payments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("request_id", ASCENDING)],
                unique=True,
                name="unique_review_fee_payment",
            ),
        ]
