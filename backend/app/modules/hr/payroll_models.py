"""Payroll periods, runs, employee calculations, payments and payslips."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.hr.enums import (
    HrPayrollEmployeeStatus,
    HrPayrollRunStatus,
    HrPayslipStatus,
)


class HrPayrollPeriod(Document):
    tenant_id: PydanticObjectId
    period_code: str = Field(max_length=64)
    period_year: int
    period_month: int = Field(ge=1, le=12)
    start_date: date
    end_date: date
    attendance_cutoff: date
    processing_date: date | None = None
    expected_payment_date: date | None = None
    is_closed: bool = False
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_payroll_periods"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("period_code", ASCENDING)], unique=True, name="unique_payroll_period"),
            IndexModel([("tenant_id", ASCENDING), ("period_year", ASCENDING), ("period_month", ASCENDING)], unique=True, name="unique_payroll_period_month"),
        ]


class HrPayrollRun(Document):
    tenant_id: PydanticObjectId
    payroll_period_id: PydanticObjectId
    run_code: str = Field(max_length=64)
    revision: int = 1
    superseded_run_id: PydanticObjectId | None = None
    reopen_reason: str | None = Field(default=None, max_length=2000)
    status: HrPayrollRunStatus = HrPayrollRunStatus.DRAFT
    calculation_version: str = "v1"
    summary: dict[str, str] = Field(default_factory=dict)
    exception_count: int = 0
    approved_by: PydanticObjectId | None = None
    approved_at: datetime | None = None
    payment_submitted_at: datetime | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_payroll_runs"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("run_code", ASCENDING)], unique=True, name="unique_payroll_run"),
            IndexModel([("tenant_id", ASCENDING), ("payroll_period_id", ASCENDING), ("revision", DESCENDING)], name="payroll_runs_by_period"),
        ]


class HrEmployeePayrollRecord(Document):
    tenant_id: PydanticObjectId
    payroll_run_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    status: HrPayrollEmployeeStatus = HrPayrollEmployeeStatus.ELIGIBLE
    exclusion_reason: str | None = Field(default=None, max_length=2000)
    salary_assignment_id: PydanticObjectId | None = None
    input_snapshot: dict[str, Any] = Field(default_factory=dict)
    earnings: dict[str, str] = Field(default_factory=dict)
    deductions: dict[str, str] = Field(default_factory=dict)
    employer_contributions: dict[str, str] = Field(default_factory=dict)
    gross_salary: str = "0"
    total_employee_deductions: str = "0"
    net_payable: str = "0"
    employer_cost: str = "0"
    warnings: list[str] = Field(default_factory=list)
    exceptions: list[str] = Field(default_factory=list)
    payment_status: str = "pending"
    payment_reference: str | None = None
    paid_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_employee_payroll_records"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("payroll_run_id", ASCENDING), ("employee_user_id", ASCENDING)],
                unique=True,
                name="unique_employee_payroll_run",
            ),
        ]


class HrPayrollAdjustment(Document):
    tenant_id: PydanticObjectId
    payroll_period_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    adjustment_code: str = Field(max_length=64)
    component_code: str = Field(max_length=64)
    amount: str
    reason: str = Field(max_length=2000)
    approved: bool = False
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_payroll_adjustments"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("adjustment_code", ASCENDING)], unique=True, name="unique_payroll_adjustment"),
        ]


class HrPayrollApprovalHistory(Document):
    tenant_id: PydanticObjectId
    payroll_run_id: PydanticObjectId
    from_status: str
    to_status: str
    actor_id: PydanticObjectId
    note: str | None = Field(default=None, max_length=2000)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_payroll_approval_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("payroll_run_id", ASCENDING), ("created_at", DESCENDING)], name="payroll_approval_history"),
        ]


class HrPayrollPaymentRecord(Document):
    tenant_id: PydanticObjectId
    payroll_run_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    employee_payroll_record_id: PydanticObjectId
    amount: str
    payment_reference: str | None = None
    finance_batch_id: str | None = None
    status: str = "submitted"
    idempotency_key: str = Field(max_length=128)
    reconciled_at: datetime | None = None
    failure_reason: str | None = Field(default=None, max_length=2000)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_payroll_payment_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)], unique=True, name="unique_payroll_payment"),
            IndexModel([("tenant_id", ASCENDING), ("payroll_run_id", ASCENDING)], name="payments_by_run"),
        ]


class HrEmployeePayslip(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    payroll_run_id: PydanticObjectId
    employee_payroll_record_id: PydanticObjectId
    period_label: str = Field(max_length=32)
    payslip_code: str = Field(max_length=64)
    status: HrPayslipStatus = HrPayslipStatus.DRAFT
    storage_key: str | None = None
    document_payload: dict[str, Any] = Field(default_factory=dict)
    current_version: int = 1
    published_at: datetime | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_payslips"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("payslip_code", ASCENDING)], unique=True, name="unique_employee_payslip"),
            IndexModel([("tenant_id", ASCENDING), ("employee_user_id", ASCENDING), ("period_label", ASCENDING)], name="payslips_by_employee_period"),
        ]


class HrEmployeePayslipVersion(Document):
    tenant_id: PydanticObjectId
    payslip_id: PydanticObjectId
    version: int
    revision_reason: str | None = Field(default=None, max_length=2000)
    document_payload: dict[str, Any] = Field(default_factory=dict)
    storage_key: str | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_payslip_versions"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("payslip_id", ASCENDING), ("version", ASCENDING)], unique=True, name="unique_payslip_version"),
        ]


class HrEmployeePayrollDocument(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId | None = None
    document_type: str = Field(max_length=64)
    title: str = Field(max_length=200)
    period_label: str | None = None
    storage_key: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_payroll_documents"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("document_type", ASCENDING), ("created_at", DESCENDING)], name="payroll_documents_by_type"),
        ]