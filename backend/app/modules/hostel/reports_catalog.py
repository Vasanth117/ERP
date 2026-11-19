"""Hostel report catalog."""

from dataclasses import dataclass

from app.authorization.permissions import Permission


@dataclass(frozen=True)
class HostelReportCatalogItem:
    report_key: str
    title: str
    category: str
    required_permission: str
    supported_formats: tuple[str, ...] = ("csv",)
    confidential: bool = False


HOSTEL_REPORT_CATALOG: list[HostelReportCatalogItem] = [
    HostelReportCatalogItem("occupancy_overview", "Hostel occupancy overview", "overview", Permission.HOSTEL_REPORTS_READ),
    HostelReportCatalogItem("applications_summary", "Applications summary", "allocation", Permission.HOSTEL_APPLICATION_READ),
    HostelReportCatalogItem("residents_current", "Current residents", "resident", Permission.HOSTEL_RESIDENT_READ),
    HostelReportCatalogItem("mess_enrollment", "Mess enrollment", "mess", Permission.HOSTEL_MESS_READ),
    HostelReportCatalogItem("mess_billing_outstanding", "Mess billing (finance refs)", "mess", Permission.HOSTEL_MESS_READ),
    HostelReportCatalogItem("visitor_logs", "Visitor logs", "visitor", Permission.HOSTEL_VISITOR_READ),
    HostelReportCatalogItem("leave_outpass", "Leave and outpass", "leave", Permission.HOSTEL_LEAVE_READ),
    HostelReportCatalogItem("maintenance_complaints", "Maintenance complaints", "maintenance", Permission.HOSTEL_MAINTENANCE_READ),
    HostelReportCatalogItem("rule_acknowledgements", "Rule acknowledgements", "rules", Permission.HOSTEL_RULES_READ),
    HostelReportCatalogItem(
        "incidents_summary",
        "Incidents summary",
        "incident",
        Permission.HOSTEL_INCIDENT_INVESTIGATE,
        confidential=True,
    ),
]


def catalog_item(report_key: str) -> HostelReportCatalogItem | None:
    for item in HOSTEL_REPORT_CATALOG:
        if item.report_key == report_key:
            return item
    return None


def catalog_for_scope(effective_permissions: frozenset) -> list[HostelReportCatalogItem]:
    if Permission.HOSTEL_REPORTS_MANAGE in effective_permissions or Permission.HOSTEL_ADMIN_MANAGE in effective_permissions:
        return list(HOSTEL_REPORT_CATALOG)
    return [c for c in HOSTEL_REPORT_CATALOG if c.required_permission in effective_permissions]