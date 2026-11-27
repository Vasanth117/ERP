"""Institutional reports hub catalogue (CA 16.01)."""

from __future__ import annotations

from dataclasses import dataclass

from app.authorization.permissions import Permission


@dataclass(frozen=True)
class ReportsHubCatalogItem:
    catalog_id: str
    report_key: str
    title: str
    required_permission: str
    group_key: str
    export_formats: tuple[str, ...]
    schedule_label: str
    detail_href: str
    module_label: str


_HUB: tuple[ReportsHubCatalogItem, ...] = (
    ReportsHubCatalogItem(
        "student_strength",
        "enrollment",
        "Student strength",
        Permission.STUDENT_ADMIN_READ.value,
        "academic",
        ("pdf", "excel"),
        "Monthly",
        "/college-admin/reports/student-reports",
        "Students",
    ),
    ReportsHubCatalogItem(
        "fee_collection",
        "finance",
        "Fee collection",
        Permission.FINANCE_ADMIN_READ.value,
        "finance_hr",
        ("excel",),
        "Weekly",
        "/college-admin/reports/finance-reports",
        "Finance",
    ),
    ReportsHubCatalogItem(
        "attendance_summary",
        "attendance",
        "Attendance summary",
        Permission.ATTENDANCE_ADMIN_READ.value,
        "academic",
        ("pdf",),
        "Daily",
        "/college-admin/reports/attendance-reports",
        "Attendance",
    ),
    ReportsHubCatalogItem(
        "exam_results",
        "examination",
        "Exam results",
        Permission.EXAMINATION_ADMIN_READ.value,
        "academic",
        ("pdf", "excel"),
        "On demand",
        "/college-admin/reports/examination-reports",
        "Examinations",
    ),
    ReportsHubCatalogItem(
        "department_snapshot",
        "dashboard",
        "Department snapshot",
        Permission.COLLEGE_DASHBOARD_READ.value,
        "academic",
        ("pdf",),
        "Monthly",
        "/college-admin/reports/department-reports",
        "Academics",
    ),
    ReportsHubCatalogItem(
        "academic_performance",
        "examination",
        "Academic performance",
        Permission.EXAMINATION_ADMIN_READ.value,
        "academic",
        ("pdf", "excel"),
        "Monthly",
        "/college-admin/reports/academic-performance-reports",
        "Academics",
    ),
    ReportsHubCatalogItem(
        "faculty_workforce",
        "hr",
        "Faculty & employee roster",
        Permission.HR_ADMIN_READ.value,
        "people",
        ("excel", "csv"),
        "Monthly",
        "/college-admin/reports/faculty-employee-reports",
        "HR",
    ),
    ReportsHubCatalogItem(
        "payroll_summary",
        "hr",
        "Payroll summary",
        Permission.HR_ADMIN_READ.value,
        "finance_hr",
        ("excel",),
        "Monthly",
        "/college-admin/reports/hr-reports",
        "HR",
    ),
    ReportsHubCatalogItem(
        "library_circulation",
        "library",
        "Library circulation",
        Permission.LIBRARY_ADMIN_READ.value,
        "library_hostel",
        ("pdf", "excel"),
        "Monthly",
        "/college-admin/reports/library-reports",
        "Library",
    ),
    ReportsHubCatalogItem(
        "hostel_occupancy",
        "hostel",
        "Hostel occupancy",
        Permission.HOSTEL_ADMIN_READ.value,
        "library_hostel",
        ("excel",),
        "Weekly",
        "/college-admin/reports/hostel-reports",
        "Hostel",
    ),
    ReportsHubCatalogItem(
        "lms_engagement",
        "lms_engagement",
        "LMS engagement",
        Permission.LMS_ADMIN_READ.value,
        "academic",
        ("excel",),
        "Monthly",
        "/college-admin/lms/lms-reports",
        "LMS",
    ),
    ReportsHubCatalogItem(
        "pending_approvals",
        "pending_approvals",
        "Pending approvals",
        Permission.COLLEGE_DASHBOARD_READ.value,
        "people",
        ("pdf",),
        "Daily",
        "/college-admin/approvals/approval-dashboard",
        "Approvals",
    ),
    ReportsHubCatalogItem(
        "finance_ledger",
        "finance",
        "Ledger summary",
        Permission.FINANCE_ADMIN_READ.value,
        "finance_hr",
        ("excel", "pdf"),
        "Monthly",
        "/college-admin/reports/finance-reports",
        "Finance",
    ),
    ReportsHubCatalogItem(
        "leave_utilisation",
        "hr",
        "Leave utilisation",
        Permission.HR_ADMIN_READ.value,
        "people",
        ("csv",),
        "Monthly",
        "/college-admin/reports/hr-reports",
        "HR",
    ),
    ReportsHubCatalogItem(
        "hostel_maintenance",
        "hostel",
        "Hostel maintenance",
        Permission.HOSTEL_ADMIN_READ.value,
        "library_hostel",
        ("pdf",),
        "Monthly",
        "/college-admin/reports/hostel-reports",
        "Hostel",
    ),
    ReportsHubCatalogItem(
        "institution_dashboard",
        "dashboard",
        "Institutional dashboard",
        Permission.COLLEGE_DASHBOARD_READ.value,
        "academic",
        ("pdf", "excel"),
        "On demand",
        "/college-admin/reports/reports-dashboard",
        "Institution",
    ),
)

_GROUP_META: dict[str, tuple[str, str, str]] = {
    "academic": ("Academic", "academic", "/college-admin/reports/academic-performance-reports"),
    "people": ("People", "people", "/college-admin/reports/student-reports"),
    "finance_hr": ("Finance and HR", "finance_hr", "/college-admin/reports/finance-reports"),
    "library_hostel": ("Library and hostel", "library_hostel", "/college-admin/reports/library-reports"),
}


def hub_items() -> tuple[ReportsHubCatalogItem, ...]:
    return _HUB


def group_meta() -> dict[str, tuple[str, str, str]]:
    return dict(_GROUP_META)