"""Phase 8 reporting and period closing API schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.accounts_finance.dashboard_schemas import FinanceDashboardOverview


class FinanceWorkspaceResponse(BaseModel):
    dashboard: FinanceDashboardOverview
    income_expense_note: str = "Student fee collections are not substitute GL income."
    net_financial_position: dict[str, Any]


class ReportCategoryInfo(BaseModel):
    category: str
    label: str
    supported_group_by: list[str] = Field(default_factory=list)
    supported_fields: list[str] = Field(default_factory=list)


class ReportPreviewResponse(BaseModel):
    category: str
    filters: dict[str, Any]
    rows: list[dict[str, Any]]
    totals: dict[str, Any] = Field(default_factory=dict)
    row_count: int


class SavedReportInput(BaseModel):
    name: str = Field(min_length=2)
    category: str
    config: dict[str, Any] = Field(default_factory=dict)
    shared: bool = False


class SavedReportRead(BaseModel):
    report_id: str
    name: str
    category: str
    config: dict[str, Any]
    shared: bool
    created_at: datetime
    updated_at: datetime


class ExportReportRequest(BaseModel):
    category: str
    export_format: str = "csv"
    filters: dict[str, Any] = Field(default_factory=dict)
    report_id: str | None = None


class FinancialYearInput(BaseModel):
    financial_year_id: str
    label: str
    start_date: date
    end_date: date
    academic_year_labels: list[str] = Field(default_factory=list)


class FinancialPeriodInput(BaseModel):
    period_code: str
    label: str
    start_date: date
    end_date: date
    financial_year_id: str | None = None
    period_type: str = "monthly"
    academic_year_label: str | None = None


class ClosingRunRead(BaseModel):
    closing_run_id: str
    period_code: str
    status: str
    exception_count: int
    checks: list[dict[str, Any]] = Field(default_factory=list)
    summary: dict[str, Any] | None = None


class ReopenRequestInput(BaseModel):
    reason: str = Field(min_length=5)
    scope_note: str | None = None