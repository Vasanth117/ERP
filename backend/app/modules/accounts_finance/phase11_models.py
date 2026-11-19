"""Phase 11 tax reporting and finance notification collections."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.accounts_finance.phase11_enums import FinanceNotificationStatus, RegulatoryReportStatus


class FinanceTaxConfigReference(Document):
    """Maps finance transaction types to authoritative HR statutory rule components (no hardcoded rates)."""

    tenant_id: PydanticObjectId
    reference_id: str
    tax_category: str
    transaction_type: str
    component_code: str
    tax_treatment: str = "collect"
    effective_from: date
    effective_to: date | None = None
    exemption_ref: str | None = None
    registration_ref: str | None = None
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_tax_config_references"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("reference_id", ASCENDING)], unique=True, name="unique_finance_tax_cfg_ref"),
            IndexModel(
                [("tenant_id", ASCENDING), ("transaction_type", ASCENDING), ("tax_category", ASCENDING)],
                name="finance_tax_cfg_by_txn",
            ),
        ]


class FinanceTaxTransactionRecord(Document):
    tenant_id: PydanticObjectId
    tax_record_id: str
    source_type: str
    source_id: str
    tax_category: str
    taxable_amount: float = Field(ge=0)
    tax_amount: float = Field(ge=0)
    rule_version_id: str | None = None
    component_code: str | None = None
    transaction_date: date
    financial_period_code: str | None = None
    reporting_status: str = "pending"
    posting_key: str
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_tax_transaction_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("tax_record_id", ASCENDING)], unique=True, name="unique_tax_tx_record"),
            IndexModel([("tenant_id", ASCENDING), ("posting_key", ASCENDING)], unique=True, name="unique_tax_posting_key"),
        ]


class FinanceTaxAdjustment(Document):
    tenant_id: PydanticObjectId
    adjustment_id: str
    tax_record_id: str
    adjustment_type: str
    amount: float
    reason: str
    effective_period: str | None = None
    status: str = "submitted"
    requested_by: PydanticObjectId
    approved_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_tax_adjustments"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("adjustment_id", ASCENDING)], unique=True, name="unique_tax_adjustment"),
        ]


class FinanceRegulatoryReport(Document):
    tenant_id: PydanticObjectId
    report_id: str
    report_type: str
    period_start: date
    period_end: date
    financial_year_id: str | None = None
    status: RegulatoryReportStatus = RegulatoryReportStatus.DRAFT
    totals: dict[str, Any] = Field(default_factory=dict)
    validation_errors: list[dict[str, Any]] = Field(default_factory=list)
    prepared_by: PydanticObjectId
    approved_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_regulatory_reports"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("report_id", ASCENDING)], unique=True, name="unique_regulatory_report"),
        ]


class FinanceRegulatoryReportVersion(Document):
    tenant_id: PydanticObjectId
    version_id: str
    report_id: str
    snapshot: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_regulatory_report_versions"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("version_id", ASCENDING)], unique=True, name="unique_reg_report_version"),
        ]


class FinanceRegulatoryFilingHistory(Document):
    tenant_id: PydanticObjectId
    filing_id: str
    report_id: str
    filing_type: str
    preparation_date: date
    review_status: str = "pending"
    approval_status: str = "pending"
    actual_filing_date: date | None = None
    external_acknowledgment: str | None = None
    filing_status: str = "prepared"
    note: str | None = None
    actor_id: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_regulatory_filing_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("filing_id", ASCENDING)], unique=True, name="unique_filing_history"),
        ]


class FinanceTaxException(Document):
    tenant_id: PydanticObjectId
    exception_id: str
    exception_type: str
    detail: str
    reference_type: str | None = None
    reference_id: str | None = None
    resolved: bool = False
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_tax_exceptions"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("exception_id", ASCENDING)], unique=True, name="unique_tax_exception"),
        ]


class FinanceReminderPolicy(Document):
    tenant_id: PydanticObjectId
    policy_id: str
    category: str
    days_before_due: int = 0
    days_after_due: int = 0
    channel: str = "in_app"
    max_reminders: int = 3
    escalation_level: int = 0
    template_subject: str = "Finance reminder"
    template_body: str = "You have a pending finance action."
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_reminder_policies"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("policy_id", ASCENDING)], unique=True, name="unique_reminder_policy"),
        ]


class FinanceScheduledReminder(Document):
    tenant_id: PydanticObjectId
    schedule_id: str
    policy_id: str
    next_run_at: datetime
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_scheduled_reminders"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("schedule_id", ASCENDING)], unique=True, name="unique_finance_schedule"),
        ]


class FinanceNotificationEvent(Document):
    tenant_id: PydanticObjectId
    notification_id: str
    category: str
    recipient_user_id: PydanticObjectId | None = None
    title: str
    body: str
    reference_type: str | None = None
    reference_id: str | None = None
    dedupe_key: str
    status: str = FinanceNotificationStatus.QUEUED.value
    channel: str = "in_app"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_notification_events"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("notification_id", ASCENDING)], unique=True, name="unique_finance_notification"),
            IndexModel([("tenant_id", ASCENDING), ("dedupe_key", ASCENDING)], unique=True, name="unique_finance_notification_dedupe"),
        ]


class FinanceNotificationHistory(Document):
    tenant_id: PydanticObjectId
    history_id: str
    notification_id: str
    status: str
    detail: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_notification_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("history_id", ASCENDING)], unique=True, name="unique_finance_notif_hist"),
        ]


class FinanceNotificationFailure(Document):
    tenant_id: PydanticObjectId
    failure_id: str
    notification_id: str
    error: str
    retry_count: int = 0
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_notification_failures"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("failure_id", ASCENDING)], unique=True, name="unique_finance_notif_failure"),
        ]


class FinanceNotificationEscalation(Document):
    tenant_id: PydanticObjectId
    escalation_id: str
    category: str
    reference_id: str
    level: int = 1
    status: str = "open"
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_notification_escalations"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("escalation_id", ASCENDING)], unique=True, name="unique_finance_escalation"),
        ]