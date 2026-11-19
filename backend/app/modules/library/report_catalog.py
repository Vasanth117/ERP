"""Library report catalogue metadata."""

from app.authorization.permissions import Permission
from app.modules.library.report_schemas import LibraryReportCatalogItem


LIBRARY_REPORT_CATALOG: list[LibraryReportCatalogItem] = [
    LibraryReportCatalogItem(
        report_type="overview",
        name="Library overview",
        description="High-level KPIs across catalogue, circulation, fines and acquisitions.",
        category="summary",
        supported_formats=["json"],
        requires_finance_permission=False,
    ),
    LibraryReportCatalogItem(
        report_type="catalogue_statistics",
        name="Catalogue statistics",
        description="Title counts by category and publication year.",
        category="catalogue",
        supported_formats=["json", "csv"],
        requires_finance_permission=False,
    ),
    LibraryReportCatalogItem(
        report_type="physical_inventory",
        name="Physical inventory",
        description="Copy counts by status and branch.",
        category="inventory",
        supported_formats=["json", "csv"],
        requires_finance_permission=False,
    ),
    LibraryReportCatalogItem(
        report_type="circulation_summary",
        name="Circulation summary",
        description="Available, issued, overdue and returned volumes in the period.",
        category="circulation",
        supported_formats=["json", "csv"],
        requires_finance_permission=False,
    ),
    LibraryReportCatalogItem(
        report_type="overdue_books",
        name="Overdue books",
        description="Active loans past due date.",
        category="circulation",
        supported_formats=["json", "csv"],
        requires_finance_permission=False,
    ),
    LibraryReportCatalogItem(
        report_type="member_activity",
        name="Member activity",
        description="Issues and returns per member in the period.",
        category="members",
        supported_formats=["json", "csv"],
        requires_finance_permission=False,
    ),
    LibraryReportCatalogItem(
        report_type="circulation_history",
        name="Issue and return history",
        description="Circulation events in the date window.",
        category="circulation",
        supported_formats=["json", "csv"],
        requires_finance_permission=False,
    ),
    LibraryReportCatalogItem(
        report_type="reservation_statistics",
        name="Reservation statistics",
        description="Reservations by status and fill rate.",
        category="reservations",
        supported_formats=["json", "csv"],
        requires_finance_permission=False,
    ),
    LibraryReportCatalogItem(
        report_type="fine_summary",
        name="Fine collection and outstanding",
        description="Assessed, collected and open fine balances.",
        category="finance",
        supported_formats=["json", "csv"],
        requires_finance_permission=True,
    ),
    LibraryReportCatalogItem(
        report_type="lost_damaged",
        name="Lost and damaged books",
        description="Copies in lost/damaged status and related damage reports.",
        category="inventory",
        supported_formats=["json", "csv"],
        requires_finance_permission=False,
    ),
    LibraryReportCatalogItem(
        report_type="acquisition_procurement",
        name="Acquisition and procurement",
        description="Requests by status in the period.",
        category="acquisition",
        supported_formats=["json", "csv"],
        requires_finance_permission=False,
    ),
    LibraryReportCatalogItem(
        report_type="digital_usage",
        name="Digital resource usage",
        description="Views and downloads from digital access logs.",
        category="digital",
        supported_formats=["json", "csv"],
        requires_finance_permission=False,
    ),
    LibraryReportCatalogItem(
        report_type="branch_performance",
        name="Branch-wise performance",
        description="Issues, returns and inventory per branch.",
        category="branches",
        supported_formats=["json", "csv"],
        requires_finance_permission=False,
    ),
    LibraryReportCatalogItem(
        report_type="popular_books",
        name="Popular / frequently borrowed",
        description="Most issued titles in the period.",
        category="catalogue",
        supported_formats=["json", "csv"],
        requires_finance_permission=False,
    ),
    LibraryReportCatalogItem(
        report_type="inventory_audit",
        name="Inventory audit and discrepancies",
        description="Open stock discrepancies and pending adjustment requests by branch.",
        category="inventory",
        supported_formats=["json", "csv"],
        requires_finance_permission=False,
    ),
]


def catalog_item(report_type: str) -> LibraryReportCatalogItem | None:
    for item in LIBRARY_REPORT_CATALOG:
        if item.report_type == report_type:
            return item
    return None


def catalog_for_role(*, can_finance: bool) -> list[LibraryReportCatalogItem]:
    if can_finance:
        return list(LIBRARY_REPORT_CATALOG)
    return [c for c in LIBRARY_REPORT_CATALOG if not c.requires_finance_permission]