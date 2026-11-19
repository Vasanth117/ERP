"""Phase 3 — online and offline payment collections."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.accounts_finance.phase3_enums import OfflinePaymentMethod, OfflinePaymentStatus, OnlinePaymentMethod, PaymentGatewayEnvironment


class PaymentGatewayConfiguration(Document):
    tenant_id: PydanticObjectId
    config_id: str
    gateway_name: str
    provider_code: str
    environment: PaymentGatewayEnvironment = PaymentGatewayEnvironment.SANDBOX
    merchant_reference: str | None = None
    currency: str = "INR"
    supported_methods: list[OnlinePaymentMethod] = Field(default_factory=list)
    webhook_url: str | None = None
    api_key_secret_ref: str | None = None
    webhook_secret_ref: str | None = None
    active: bool = False
    connection_status: str = "unknown"
    metadata: dict[str, Any] = Field(default_factory=dict)
    updated_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "payment_gateway_configurations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("config_id", ASCENDING)],
                unique=True,
                name="unique_payment_gateway_config",
            ),
        ]


class OnlinePaymentOrder(Document):
    tenant_id: PydanticObjectId
    order_id: str
    student_user_id: PydanticObjectId
    payer_user_id: PydanticObjectId
    invoice_id: str | None = None
    demand_id: str
    merchant_order_id: str
    amount: float = Field(ge=0)
    currency: str = "INR"
    gateway_config_id: str
    status: str = "initiated"
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "online_payment_orders"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("order_id", ASCENDING)],
                unique=True,
                name="unique_online_payment_order",
            ),
            IndexModel([("tenant_id", ASCENDING), ("merchant_order_id", ASCENDING)], unique=True, name="unique_merchant_order"),
        ]


class OnlinePaymentAttempt(Document):
    tenant_id: PydanticObjectId
    attempt_id: str
    order_id: str
    transaction_id: str
    payment_method: OnlinePaymentMethod = OnlinePaymentMethod.OTHER
    idempotency_key: str
    status: str = "initiated"
    failure_code: str | None = None
    failure_detail: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    verified_at: datetime | None = None

    class Settings:
        name = "online_payment_attempts"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("attempt_id", ASCENDING)],
                unique=True,
                name="unique_online_payment_attempt",
            ),
            IndexModel([("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)], unique=True, name="unique_online_idempotency"),
            IndexModel([("tenant_id", ASCENDING), ("transaction_id", ASCENDING)], name="attempts_by_tx"),
        ]


class PaymentGatewayWebhookEvent(Document):
    tenant_id: PydanticObjectId
    event_id: str
    provider_event_id: str
    gateway_config_id: str | None = None
    transaction_id: str | None = None
    signature_valid: bool = False
    processed: bool = False
    duplicate: bool = False
    payload_hash: str
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "payment_gateway_webhook_events"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("provider_event_id", ASCENDING)],
                unique=True,
                name="unique_provider_webhook_event",
            ),
        ]


class PaymentVerificationHistory(Document):
    tenant_id: PydanticObjectId
    transaction_id: str
    step: str
    outcome: str
    detail: str | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "payment_verification_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("transaction_id", ASCENDING), ("created_at", DESCENDING)], name="payment_verify_trail"),
        ]


class PaymentGatewayFailure(Document):
    tenant_id: PydanticObjectId
    failure_id: str
    transaction_id: str | None = None
    order_id: str | None = None
    code: str
    message: str
    recoverable: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "payment_gateway_failures"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("failure_id", ASCENDING)], unique=True, name="unique_gateway_failure"),
        ]


class OfflinePaymentRecord(Document):
    tenant_id: PydanticObjectId
    record_id: str
    student_user_id: PydanticObjectId
    invoice_id: str | None = None
    demand_id: str
    transaction_id: str | None = None
    amount: float = Field(ge=0)
    payment_method: OfflinePaymentMethod
    payment_date: date
    status: OfflinePaymentStatus = OfflinePaymentStatus.AWAITING_VERIFICATION
    instrument_reference: str | None = None
    bank_name: str | None = None
    branch: str | None = None
    collection_location: str | None = None
    collected_by: PydanticObjectId | None = None
    remarks: str | None = None
    document_ref: str | None = None
    batch_id: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "offline_payment_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("record_id", ASCENDING)], unique=True, name="unique_offline_payment"),
            IndexModel([("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("status", ASCENDING)], name="offline_by_student"),
        ]


class OfflinePaymentVerificationHistory(Document):
    tenant_id: PydanticObjectId
    record_id: str
    action: str
    from_status: str | None = None
    to_status: str | None = None
    actor_id: PydanticObjectId
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "offline_payment_verification_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("record_id", ASCENDING), ("created_at", DESCENDING)], name="offline_verify_trail"),
        ]


class OfflineCollectionBatch(Document):
    tenant_id: PydanticObjectId
    batch_id: str
    batch_date: date
    counter_code: str | None = None
    cashier_user_id: PydanticObjectId | None = None
    payment_method: OfflinePaymentMethod | None = None
    total_amount: float = Field(default=0, ge=0)
    record_count: int = 0
    verified: bool = False
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "offline_collection_batches"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("batch_id", ASCENDING)], unique=True, name="unique_collection_batch"),
        ]


class OfflineCollectionHandoverRecord(Document):
    tenant_id: PydanticObjectId
    handover_id: str
    batch_id: str
    from_user_id: PydanticObjectId
    to_user_id: PydanticObjectId | None = None
    amount: float = Field(ge=0)
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "offline_collection_handover_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("handover_id", ASCENDING)], unique=True, name="unique_handover"),
        ]


class OfflinePaymentInstrument(Document):
    tenant_id: PydanticObjectId
    instrument_id: str
    record_id: str
    instrument_type: OfflinePaymentMethod
    instrument_number: str | None = None
    issue_date: date | None = None
    clearance_status: str = "pending"
    bounce_reason: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "offline_payment_instruments"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("instrument_id", ASCENDING)], unique=True, name="unique_offline_instrument"),
        ]


class OfflinePaymentReversal(Document):
    tenant_id: PydanticObjectId
    reversal_id: str
    record_id: str
    transaction_id: str | None = None
    reason: str
    actor_id: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "offline_payment_reversals"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("reversal_id", ASCENDING)], unique=True, name="unique_offline_reversal"),
        ]