"""Payroll API schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.hr.enums import HrPayrollRunStatus, HrPayslipStatus
from app.modules.hr.payroll_models import HrEmployeePayrollRecord, HrPayrollPeriod, HrPayrollRun


class PayrollPeriodCreate(BaseModel):
    period_year: int
    period_month: int = Field(ge=1, le=12)
    start_date: date
    end_date: date
    attendance_cutoff: date
    processing_date: date | None = None
    expected_payment_date: date | None = None


class PayrollPeriodRead(BaseModel):
    id: str
    period_code: str
    period_year: int
    period_month: int

    @classmethod
    def from_document(cls, doc: HrPayrollPeriod) -> "PayrollPeriodRead":
        return cls(id=str(doc.id), period_code=doc.period_code, period_year=doc.period_year, period_month=doc.period_month)


class PayrollRunCreate(BaseModel):
    payroll_period_id: str
    reopen_reason: str | None = None


class PayrollRunRead(BaseModel):
    id: str
    run_code: str
    status: HrPayrollRunStatus
    revision: int

    @classmethod
    def from_document(cls, doc: HrPayrollRun) -> "PayrollRunRead":
        return cls(id=str(doc.id), run_code=doc.run_code, status=doc.status, revision=doc.revision)


class PayrollTransition(BaseModel):
    target_status: HrPayrollRunStatus
    note: str | None = None


class PayrollAdjustmentCreate(BaseModel):
    payroll_period_id: str
    employee_user_id: str
    component_code: str
    amount: str
    reason: str = Field(min_length=1, max_length=2000)


class EmployeePayrollPreview(BaseModel):
    employee_user_id: str
    status: str
    gross_salary: str
    net_payable: str
    warnings: list[str] = Field(default_factory=list)
    exceptions: list[str] = Field(default_factory=list)
    input_snapshot: dict[str, Any] = Field(default_factory=dict)


class PayrollPreview(BaseModel):
    run_id: str
    status: HrPayrollRunStatus
    employees: list[EmployeePayrollPreview]
    summary: dict[str, str]
    exception_count: int


class PaymentConfirm(BaseModel):
    employee_user_id: str
    payment_reference: str = Field(min_length=1, max_length=128)
    finance_batch_id: str | None = None


class PayrollReports(BaseModel):
    gross_total: str = "0"
    net_total: str = "0"
    employer_cost_total: str = "0"
    department_totals: dict[str, str] = Field(default_factory=dict)
    failed_payments: int = 0
    exception_count: int = 0


class PayslipGenerateRequest(BaseModel):
    payroll_run_id: str
    employee_user_ids: list[str] | None = None


class PayslipRead(BaseModel):
    id: str
    payslip_code: str
    employee_user_id: str
    period_label: str
    status: HrPayslipStatus

    @classmethod
    def from_record(cls, employee_user_id: str, period_label: str, doc) -> "PayslipRead":
        return cls(
            id=str(doc.id),
            payslip_code=doc.payslip_code,
            employee_user_id=employee_user_id,
            period_label=period_label,
            status=doc.status,
        )


class PayslipRevise(BaseModel):
    revision_reason: str = Field(min_length=1, max_length=2000)