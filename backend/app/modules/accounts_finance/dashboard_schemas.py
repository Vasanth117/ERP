"""Finance dashboard schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class MetricAvailability(BaseModel):
    available: bool = True
    reason: str | None = None


class DashboardMetric(BaseModel):
    value: float | int = 0
    availability: MetricAvailability = Field(default_factory=MetricAvailability)


class FinanceDashboardFilters(BaseModel):
    financial_year: str | None = None
    academic_year_label: str | None = None
    semester_label: str | None = None
    programme_code: str | None = None
    department_id: str | None = None
    fee_category_code: str | None = None
    invoice_status: str | None = None
    payment_status: str | None = None
    payment_method: str | None = None
    campus_id: str | None = None
    date_from: date | None = None
    date_to: date | None = None


class DrillDownLink(BaseModel):
    resource: str
    path: str
    query: dict[str, Any] = Field(default_factory=dict)


class FinancialOverviewSection(BaseModel):
    total_fees_assessed: DashboardMetric
    total_invoices_generated: DashboardMetric
    total_billed_amount: DashboardMetric
    total_verified_collections: DashboardMetric
    total_outstanding_amount: DashboardMetric
    total_overdue_amount: DashboardMetric
    total_pending_payments: DashboardMetric
    total_failed_payments: DashboardMetric
    total_reversed_payments: DashboardMetric
    total_refunds_initiated: DashboardMetric
    total_refunds_completed: DashboardMetric
    total_scholarship_awards: DashboardMetric
    total_concessions_and_waivers: DashboardMetric
    net_fee_collection: DashboardMetric
    collection_percentage: DashboardMetric


class StudentFeeOverviewSection(BaseModel):
    students_with_obligations: DashboardMetric
    students_fully_paid: DashboardMetric
    students_partially_paid: DashboardMetric
    students_outstanding: DashboardMetric
    students_overdue_invoices: DashboardMetric
    students_scholarships: DashboardMetric
    students_concessions: DashboardMetric
    students_installment_plans: DashboardMetric
    students_payment_arrangements: DashboardMetric


class PaymentOverviewSection(BaseModel):
    online_payments: DashboardMetric
    offline_payments: DashboardMetric
    verified_transactions: DashboardMetric
    pending_verification: DashboardMetric
    failed_transactions: DashboardMetric
    suspicious_duplicates: DashboardMetric
    gateway_collections: dict[str, float]
    daily_collections: list[dict[str, Any]]
    payment_method_summary: dict[str, float]
    reconciliation_pending: DashboardMetric


class InvoiceOverviewSection(BaseModel):
    draft_invoices: DashboardMetric
    issued_invoices: DashboardMetric
    partially_paid_invoices: DashboardMetric
    fully_paid_invoices: DashboardMetric
    overdue_invoices: DashboardMetric
    cancelled_invoices: DashboardMetric
    credit_debit_adjustments: DashboardMetric
    upcoming_fee_demands: DashboardMetric


class ScholarshipConcessionSection(BaseModel):
    applications_awaiting_review: DashboardMetric
    approved_scholarships: DashboardMetric
    rejected_applications: DashboardMetric
    active_concessions: DashboardMetric
    pending_waiver_approvals: DashboardMetric
    total_approved_financial_aid: DashboardMetric
    aid_utilization_amount: DashboardMetric


class RefundOverviewSection(BaseModel):
    refund_requests: DashboardMetric
    pending_approval: DashboardMetric
    approved_refunds: DashboardMetric
    processing_refunds: DashboardMetric
    completed_refunds: DashboardMetric
    failed_refunds: DashboardMetric
    reversal_transactions: DashboardMetric


class AccountingOverviewSection(BaseModel):
    total_income: DashboardMetric
    total_expenses: DashboardMetric
    outstanding_receivables: DashboardMetric
    payables: DashboardMetric
    bank_cash_balances: DashboardMetric
    journal_entries_pending: DashboardMetric
    financial_period_status: DashboardMetric
    reconciliation_exceptions: DashboardMetric


class FinanceDashboardOverview(BaseModel):
    generated_at: datetime
    filters: FinanceDashboardFilters
    financial: FinancialOverviewSection
    student_fees: StudentFeeOverviewSection
    payments: PaymentOverviewSection
    invoices: InvoiceOverviewSection
    scholarships: ScholarshipConcessionSection
    refunds: RefundOverviewSection
    accounting: AccountingOverviewSection
    drill_downs: list[DrillDownLink] = Field(default_factory=list)