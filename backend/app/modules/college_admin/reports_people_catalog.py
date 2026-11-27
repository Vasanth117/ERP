"""People reports module catalog (CA 16 People)."""

from __future__ import annotations

from dataclasses import dataclass

from app.authorization.permissions import Permission

from app.modules.college_admin.reports_academic_catalog import ReportsAcademicPageMeta, ReportsAcademicSeedRow, _rows


_PAGE_META: dict[str, ReportsAcademicPageMeta] = {
    "faculty-employee": ReportsAcademicPageMeta(
        "faculty-employee",
        "Faculty & Employee Reports",
        "Headcount, workload and vacancies",
        "hr",
        Permission.HR_ADMIN_READ,
    ),
    "hr": ReportsAcademicPageMeta(
        "hr",
        "HR Reports",
        "Leave, payroll and attrition",
        "hr",
        Permission.HR_ADMIN_READ,
    ),
}


def page_meta(page_key: str) -> ReportsAcademicPageMeta | None:
    return _PAGE_META.get(page_key)


_PAGE_ROWS: dict[str, tuple[ReportsAcademicSeedRow, ...]] = {
    "faculty-employee": _rows(
        (
            ("faculty_workload", "Faculty workload", ("excel",), "Monthly", "term"),
            ("headcount_by_department", "Headcount by department", ("pdf",), "Monthly", "month"),
            ("vacancy_recruitment", "Vacancy and recruitment", ("excel",), "Weekly", "month"),
            ("contract_expiry", "Contract expiry", ("pdf",), "Weekly", "on_demand"),
            ("faculty_directory", "Faculty directory export", ("pdf", "excel"), "Monthly", "month"),
            ("employee_status", "Employee status summary", ("excel",), "Monthly", "month"),
            ("workload_rebalance", "Workload rebalance log", ("excel",), "On demand", "term"),
            ("probation_due", "Probation review due", ("pdf",), "Weekly", "month"),
            ("designation_mix", "Designation mix", ("pdf",), "Quarterly", "year"),
            ("teaching_load", "Teaching load hours", ("excel",), "Monthly", "term"),
            ("non_teaching_staff", "Non-teaching staff list", ("excel",), "Monthly", "month"),
            ("document_verification", "Document verification status", ("pdf",), "Weekly", "month"),
            ("faculty_transfers", "Faculty transfer history", ("excel",), "Quarterly", "year"),
            ("retirement_forecast", "Retirement forecast", ("pdf",), "Yearly", "year"),
            ("contract_renewals", "Contract renewals", ("pdf",), "Weekly", "month"),
            ("department_faculty_gap", "Department faculty gap", ("excel",), "Monthly", "month"),
        ),
    ),
    "hr": _rows(
        (
            ("leave_summary", "Leave summary", ("excel",), "Monthly", "month"),
            ("payroll_register", "Payroll register", ("pdf", "excel"), "Monthly", "month"),
            ("attrition", "Attrition", ("pdf",), "Quarterly", "year"),
            ("appraisal_status", "Appraisal status", ("excel",), "Weekly", "year"),
            ("onboarding_progress", "Onboarding progress", ("excel",), "Monthly", "month"),
            ("benefit_claims", "Benefit claims", ("pdf",), "Monthly", "month"),
            ("leave_balance", "Leave balance statement", ("excel",), "On demand", "year"),
            ("payroll_variance", "Payroll variance", ("excel",), "Monthly", "month"),
            ("attendance_hr_lock", "Attendance lock before payroll", ("pdf",), "Monthly", "month"),
            ("exit_interviews", "Exit interviews", ("pdf",), "Quarterly", "year"),
            ("recruitment_funnel", "Recruitment funnel", ("excel",), "Weekly", "month"),
            ("salary_structure", "Salary structure roster", ("excel",), "On demand", "year"),
            ("compliance_training", "Compliance training", ("pdf",), "Quarterly", "year"),
            ("overtime_summary", "Overtime summary", ("excel",), "Monthly", "month"),
            ("holiday_calendar", "Holiday calendar usage", ("pdf",), "Yearly", "year"),
            ("disciplinary_cases", "Disciplinary cases", ("pdf",), "Quarterly", "year"),
        ),
    ),
}


def page_rows(page_key: str) -> tuple[ReportsAcademicSeedRow, ...]:
    return _PAGE_ROWS.get(page_key, ())