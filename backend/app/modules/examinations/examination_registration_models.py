"""Central examination registration windows and fee payment records."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel

from app.common.time import utcnow
from app.modules.examinations.examination_registration_enums import ExaminationFeePaymentStatus


class ExaminationRegistrationWindow(Document):
    tenant_id: PydanticObjectId
    season_id: str
    registration_open_at: datetime
    registration_close_at: datetime
    cancellation_deadline: datetime | None = None
    fee_required: bool = True
    fee_amount: float = Field(default=0, ge=0)
    fee_code: str = "exam_fee"
    allow_arrear_registration: bool = True
    published: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "examination_registration_windows"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("season_id", ASCENDING)],
                unique=True,
                name="unique_exam_registration_window",
            ),
        ]


class ExaminationFeePayment(Document):
    """Authoritative fee status — never trust client payment callbacks alone."""

    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    season_id: str
    fee_code: str
    amount: float = Field(ge=0)
    currency: str = "INR"
    status: ExaminationFeePaymentStatus = ExaminationFeePaymentStatus.PENDING
    provider_reference: str | None = None
    verified_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "examination_fee_payments"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("student_user_id", ASCENDING),
                    ("season_id", ASCENDING),
                    ("fee_code", ASCENDING),
                ],
                unique=True,
                name="unique_exam_fee_per_student_season",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("status", ASCENDING)],
                name="exam_fee_by_status",
            ),
        ]
