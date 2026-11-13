"""Student finance portal (not authoritative ledger)."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class StudentFeeViewPreferences(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    show_installments: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_fee_view_preferences"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING)],
                unique=True,
                name="unique_fee_view_prefs",
            ),
        ]


class StudentPaymentAttempt(Document):
    """Client-initiated payment attempts linked to central `payment_transactions`."""

    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    idempotency_key: str
    transaction_id: str
    demand_id: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_payment_attempts"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)],
                unique=True,
                name="unique_payment_attempt",
            ),
        ]


class StudentScholarshipApplication(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    application_id: str
    programme_id: str
    statement: str | None = Field(default=None, max_length=4000)
    status: str = "submitted"
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_scholarship_applications"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("application_id", ASCENDING)],
                unique=True,
                name="unique_student_scholarship_app",
            ),
        ]


class StudentFinancialDocumentReference(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    document_id: str
    document_type: str
    last_viewed_at: datetime | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_financial_document_references"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("document_id", ASCENDING)],
                unique=True,
                name="unique_financial_doc_ref",
            ),
        ]


class StudentPaymentNotificationLog(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    title: str
    body: str
    demand_id: str | None = None
    read_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_payment_notification_logs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="payment_notifications",
            ),
        ]
