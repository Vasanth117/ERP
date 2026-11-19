"""HR report catalog — keys and permission requirements."""

from dataclasses import dataclass

from app.authorization.permissions import Permission


@dataclass(frozen=True)
class HrReportCatalogItem:
    report_key: str
    title: str
    category: str
    required_permission: str
    supported_formats: tuple[str, ...] = ("csv",)


HR_REPORT_CATALOG: list[HrReportCatalogItem] = [
    HrReportCatalogItem("employee_master", "Employee master", "employee", Permission.HR_REPORTS_READ),
    HrReportCatalogItem("department_employees", "Department-wise employees", "employee", Permission.HR_REPORTS_READ),
    HrReportCatalogItem("leave_summary", "Leave summary", "leave", Permission.HR_LEAVE_READ),
    HrReportCatalogItem("attendance_monthly", "Monthly attendance", "attendance", Permission.HR_ATTENDANCE_READ),
    HrReportCatalogItem("payroll_summary", "Payroll summary", "payroll", Permission.HR_PAYROLL_READ),
    HrReportCatalogItem("benefits_claims", "Benefits and claims", "benefits", Permission.HR_BENEFITS_READ),
    HrReportCatalogItem("tax_declaration_status", "Tax declaration status", "statutory", Permission.HR_TAX_READ),
    HrReportCatalogItem("performance_reviews", "Performance reviews", "performance", Permission.HR_PERFORMANCE_READ),
    HrReportCatalogItem("training_completion", "Training completion", "training", Permission.HR_TRAINING_READ),
    HrReportCatalogItem("recruitment_pipeline", "Recruitment pipeline", "recruitment", Permission.HR_RECRUITMENT_READ),
    HrReportCatalogItem("onboarding_status", "Onboarding status", "onboarding", Permission.HR_ONBOARDING_READ),
]


def catalog_item(report_key: str) -> HrReportCatalogItem | None:
    for item in HR_REPORT_CATALOG:
        if item.report_key == report_key:
            return item
    return None


def catalog_for_scope(effective_permissions: frozenset) -> list[HrReportCatalogItem]:
    from app.authorization.permissions import Permission

    if Permission.HR_REPORTS_MANAGE in effective_permissions or Permission.HR_ADMIN_MANAGE in effective_permissions:
        return list(HR_REPORT_CATALOG)
    return [c for c in HR_REPORT_CATALOG if c.required_permission in effective_permissions]