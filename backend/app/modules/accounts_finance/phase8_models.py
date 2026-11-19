"""Phase 8 saved reports and financial period closing."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.accounts_finance.phase8_enums import ClosingRunStatus


class FinancialYear(Document):
    tenant_id: PydanticObjectId
    financial_year_id: str
    label: str
    start_date: date
    end_date: date
    academic_year_labels: list[str] = Field(default_factory=list)
    status: str = "open"
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "financial_years"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("financial_year_id", ASCENDING)], unique=True, name="unique_financial_year"),
        ]


class FinancialPeriodClosingRun(Document):
    tenant_id: PydanticObjectId
    closing_run_id: str
    period_code: str
    status: ClosingRunStatus = ClosingRunStatus.VALIDATION
    initiated_by: PydanticObjectId
    approved_by: PydanticObjectId | None = None
    exception_count: int = 0
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "financial_period_closing_runs"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("closing_run_id", ASCENDING)], unique=True, name="unique_closing_run"),
        ]


class FinancialPeriodClosingCheck(Document):
    tenant_id: PydanticObjectId
    check_id: str
    closing_run_id: str
    check_type: str
    severity: str = "warning"
    detail: str
    reference_id: str | None = None
    resolved: bool = False
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "financial_period_closing_checks"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("check_id", ASCENDING)], unique=True, name="unique_closing_check"),
        ]


class FinancialPeriodClosingSummary(Document):
    tenant_id: PydanticObjectId
    summary_id: str
    closing_run_id: str
    period_code: str
    opening_balances: dict[str, Any] = Field(default_factory=dict)
    period_collections: float = 0.0
    period_charges: float = 0.0
    period_refunds: float = 0.0
    period_adjustments: float = 0.0
    closing_balances: dict[str, Any] = Field(default_factory=dict)
    pending_exceptions: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "financial_period_closing_summaries"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("summary_id", ASCENDING)], unique=True, name="unique_closing_summary"),
        ]


class FinancialPeriodReopeningRequest(Document):
    tenant_id: PydanticObjectId
    request_id: str
    period_code: str
    reason: str
    scope_note: str | None = None
    status: str = "submitted"
    requested_by: PydanticObjectId
    approved_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "financial_period_reopening_requests"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("request_id", ASCENDING)], unique=True, name="unique_reopen_request"),
        ]


class FinancialPeriodStatusHistory(Document):
    tenant_id: PydanticObjectId
    history_id: str
    period_code: str
    from_status: str | None = None
    to_status: str
    actor_id: PydanticObjectId | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "financial_period_status_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("history_id", ASCENDING)], unique=True, name="unique_period_status_hist"),
        ]


class FinanceSavedReport(Document):
    tenant_id: PydanticObjectId
    report_id: str
    name: str
    category: str
    config: dict[str, Any] = Field(default_factory=dict)
    created_by: PydanticObjectId
    shared: bool = False
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_saved_reports"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("report_id", ASCENDING)], unique=True, name="unique_saved_report"),
        ]


class FinanceScheduledReport(Document):
    tenant_id: PydanticObjectId
    schedule_id: str
    report_id: str
    cron_hint: str | None = None
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_scheduled_reports"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("schedule_id", ASCENDING)], unique=True, name="unique_scheduled_report"),
        ]


class FinanceReportExecutionHistory(Document):
    tenant_id: PydanticObjectId
    execution_id: str
    report_id: str | None = None
    category: str
    export_format: str | None = None
    row_count: int = 0
    actor_id: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "finance_report_execution_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("execution_id", ASCENDING)], unique=True, name="unique_report_execution"),
        ]