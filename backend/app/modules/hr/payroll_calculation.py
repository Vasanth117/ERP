"""Payroll calculation with Decimal arithmetic and input snapshots."""

from calendar import monthrange
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, GTE, LTE

from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.hr.attendance_schedule_models import HrEmployeeAttendanceMonthlySummary, HrEmployeeAttendanceRecord
from app.modules.hr.enums import EmployeeAttendanceDayStatus, HrSalaryAssignmentStatus, LeaveRequestStatus
from app.modules.hr.models import LeaveRequest
from app.modules.hr.salary_calculation import calculate_structure
from app.modules.hr.salary_structure_models import HrEmployeeSalaryAssignment, HrSalaryTemplate


def _d(value: str | float | int) -> Decimal:
    return Decimal(str(value))


def _money(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def proration_factor(*, period_start: date, period_end: date, join_date: date | None, exit_date: date | None) -> Decimal:
    days_in_period = (period_end - period_start).days + 1
    start = max(period_start, join_date) if join_date else period_start
    end = min(period_end, exit_date) if exit_date else period_end
    if end < start:
        return Decimal("0")
    active_days = (end - start).days + 1
    return (Decimal(active_days) / Decimal(days_in_period)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


async def gather_attendance_inputs(tenant_id: PydanticObjectId, employee_user_id: PydanticObjectId, start: date, end: date) -> dict[str, Any]:
    records = await HrEmployeeAttendanceRecord.find(
        Eq(HrEmployeeAttendanceRecord.tenant_id, tenant_id),
        Eq(HrEmployeeAttendanceRecord.employee_user_id, employee_user_id),
        GTE(HrEmployeeAttendanceRecord.attendance_date, start),
        LTE(HrEmployeeAttendanceRecord.attendance_date, end),
    ).to_list()
    present = 0
    absent = 0
    overtime_minutes = 0
    for row in records:
        if row.status in {
            EmployeeAttendanceDayStatus.PRESENT,
            EmployeeAttendanceDayStatus.LATE,
            EmployeeAttendanceDayStatus.HALF_DAY,
            EmployeeAttendanceDayStatus.WORK_FROM_HOME,
        }:
            present += 1
        elif row.status == EmployeeAttendanceDayStatus.ABSENT:
            absent += 1
        overtime_minutes += row.overtime_minutes
    monthly = await HrEmployeeAttendanceMonthlySummary.find_one(
        Eq(HrEmployeeAttendanceMonthlySummary.tenant_id, tenant_id),
        Eq(HrEmployeeAttendanceMonthlySummary.employee_user_id, employee_user_id),
        Eq(HrEmployeeAttendanceMonthlySummary.period_year, start.year),
        Eq(HrEmployeeAttendanceMonthlySummary.period_month, start.month),
    )
    return {
        "present_days": present,
        "absent_days": absent,
        "overtime_minutes": overtime_minutes,
        "monthly_summary_status": monthly.status.value if monthly else None,
    }


async def gather_leave_inputs(tenant_id: PydanticObjectId, employee_user_id: PydanticObjectId, start: date, end: date) -> dict[str, Any]:
    leaves = await LeaveRequest.find(
        Eq(LeaveRequest.tenant_id, tenant_id),
        Eq(LeaveRequest.employee_user_id, employee_user_id),
        Eq(LeaveRequest.status, LeaveRequestStatus.APPROVED),
    ).to_list()
    paid = Decimal("0")
    unpaid = Decimal("0")
    for leave in leaves:
        if leave.end_date < start or leave.start_date > end:
            continue
        portion = _d(leave.working_days or 0)
        if leave.leave_type.lower() in {"unpaid", "loss_of_pay", "lop"}:
            unpaid += portion
        else:
            paid += portion
    return {"paid_leave_days": str(paid), "unpaid_leave_days": str(unpaid)}


async def calculate_employee_payroll(
    *,
    tenant_id: PydanticObjectId,
    employee: EmployeeRecord,
    period_start: date,
    period_end: date,
    adjustments: list[dict[str, Any]],
    statutory_rates: dict[str, str],
    statutory_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    warnings: list[str] = []
    exceptions: list[str] = []
    eligibility = {"eligible": True, "reason": None}

    if employee.employment_status not in {
        FacultyEmploymentStatus.ACTIVE,
        FacultyEmploymentStatus.CONFIRMED,
        FacultyEmploymentStatus.NOTICE_PERIOD,
        FacultyEmploymentStatus.PROBATION,
    }:
        return {
            "eligible": False,
            "exclusion_reason": f"Status {employee.employment_status.value}",
            "warnings": warnings,
            "exceptions": exceptions,
        }

    assignment = await HrEmployeeSalaryAssignment.find_one(
        Eq(HrEmployeeSalaryAssignment.tenant_id, tenant_id),
        Eq(HrEmployeeSalaryAssignment.employee_user_id, employee.user_id),
        Eq(HrEmployeeSalaryAssignment.status, HrSalaryAssignmentStatus.ACTIVE),
    )
    if assignment is None:
        exceptions.append("missing_salary_structure")
        return {"eligible": False, "exclusion_reason": "No active salary assignment", "warnings": warnings, "exceptions": exceptions}

    template = await HrSalaryTemplate.get(assignment.template_id)
    component_defs = template.component_lines if template else []
    base_calc = calculate_structure(component_defs=component_defs, amounts=assignment.component_amounts)

    join_date = None
    profile_snapshot = (employee.confidential_hr or {}).get("joining_date")
    if profile_snapshot:
        join_date = date.fromisoformat(profile_snapshot)
    exit_date = None
    lwd = (employee.confidential_hr or {}).get("last_working_date")
    if lwd:
        exit_date = date.fromisoformat(lwd)

    factor = proration_factor(period_start=period_start, period_end=period_end, join_date=join_date, exit_date=exit_date)
    if factor <= 0:
        return {"eligible": False, "exclusion_reason": "Not employed in payroll period", "warnings": warnings, "exceptions": exceptions}

    attendance = await gather_attendance_inputs(tenant_id, employee.user_id, period_start, period_end)
    leave_info = await gather_leave_inputs(tenant_id, employee.user_id, period_start, period_end)

    earnings = {k: _money(_d(v) * factor) for k, v in base_calc["computed_amounts"].items() if k in assignment.component_amounts}
    deductions: dict[str, str] = {}
    employer: dict[str, str] = {}

    gross = sum(_d(v) for v in earnings.values())
    for line in component_defs:
        code = str(line.get("component_code"))
        if line.get("category") == "deduction":
            if line.get("calc_type") == "percentage" and line.get("statutory_ref"):
                rate_key = str(line.get("statutory_ref"))
                rate = _d(statutory_rates.get(rate_key, "0"))
                basis = _d(earnings.get(str(line.get("percentage_of", "basic")), earnings.get("basic", "0")))
                deductions[code] = _money(basis * rate / Decimal("100"))
            elif code in base_calc["computed_amounts"]:
                deductions[code] = _money(_d(base_calc["computed_amounts"][code]) * factor)
        if line.get("employer_contribution") and line.get("statutory_ref"):
            rate_key = str(line["statutory_ref"])
            rate = _d(statutory_rates.get(rate_key, "0"))
            basis = _d(earnings.get("basic", "0"))
            employer[code] = _money(basis * rate / Decimal("100"))

    unpaid_days = _d(leave_info["unpaid_leave_days"])
    if unpaid_days > 0:
        daily = gross / Decimal(max(1, (period_end - period_start).days + 1))
        deductions["unpaid_leave"] = _money(daily * unpaid_days)

    ot_minutes = Decimal(attendance["overtime_minutes"])
    if ot_minutes > 0:
        hourly = gross / Decimal("208")
        earnings["overtime"] = _money(hourly * (ot_minutes / Decimal("60")))

    for adj in adjustments:
        earnings[adj["component_code"]] = _money(_d(earnings.get(adj["component_code"], "0")) + _d(adj["amount"]))

    gross = sum(_d(v) for v in earnings.values())
    total_deductions = sum(_d(v) for v in deductions.values())
    net = gross - total_deductions
    employer_total = sum(_d(v) for v in employer.values())

    if net < 0:
        exceptions.append("negative_net_salary")
        warnings.append("Net salary is negative after deductions")

    if attendance["monthly_summary_status"] is None:
        warnings.append("attendance_month_not_closed")

    if not statutory_rates:
        warnings.append("missing_statutory_configuration")

    return {
        "eligible": True,
        "eligibility": eligibility,
        "salary_assignment_id": assignment.id,
        "input_snapshot": {
            "assignment_id": str(assignment.id),
            "template_version": assignment.template_version,
            "proration_factor": str(factor),
            "attendance": attendance,
            "leave": leave_info,
            "statutory_rates_keys": list(statutory_rates.keys()),
            "statutory_rule_refs": (statutory_meta or {}).get("rule_versions", []),
            "statutory_source": (statutory_meta or {}).get("source"),
        },
        "earnings": earnings,
        "deductions": deductions,
        "employer_contributions": employer,
        "gross_salary": _money(gross),
        "total_employee_deductions": _money(total_deductions),
        "net_payable": _money(net),
        "employer_cost": _money(gross + employer_total),
        "warnings": warnings,
        "exceptions": exceptions,
    }