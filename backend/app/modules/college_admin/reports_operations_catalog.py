"""Operations reports module catalog (CA 16 Operations)."""

from __future__ import annotations

from app.authorization.permissions import Permission

from app.modules.college_admin.reports_academic_catalog import ReportsAcademicPageMeta, ReportsAcademicSeedRow, _rows

_PAGE_META: dict[str, ReportsAcademicPageMeta] = {
    "finance": ReportsAcademicPageMeta(
        "finance",
        "Finance Reports",
        "Collection, dues and refunds",
        "finance",
        Permission.FINANCE_ADMIN_READ,
    ),
    "library": ReportsAcademicPageMeta(
        "library",
        "Library Reports",
        "Circulation and usage",
        "library",
        Permission.LIBRARY_ADMIN_READ,
    ),
    "hostel": ReportsAcademicPageMeta(
        "hostel",
        "Hostel Reports",
        "Occupancy, fees and incidents",
        "hostel",
        Permission.HOSTEL_ADMIN_READ,
    ),
}


def page_meta(page_key: str) -> ReportsAcademicPageMeta | None:
    return _PAGE_META.get(page_key)


_PAGE_ROWS: dict[str, tuple[ReportsAcademicSeedRow, ...]] = {
    "finance": _rows(
        (
            ("fee_collection", "Fee collection", ("pdf", "excel"), "Weekly", "year"),
            ("outstanding_dues", "Outstanding dues", ("csv",), "Daily", "on_demand"),
            ("refund_register", "Refund register", ("excel",), "Monthly", "year"),
            ("scholarship_disbursal", "Scholarship disbursal", ("excel",), "Monthly", "year"),
            ("payment_mode_summary", "Payment mode summary", ("pdf", "excel"), "Monthly", "month"),
            ("reconciliation_exceptions", "Reconciliation exceptions", ("excel",), "Weekly", "month"),
            ("demand_vs_collection", "Demand vs collection", ("pdf",), "Monthly", "year"),
            ("concession_register", "Concession register", ("excel",), "Monthly", "year"),
            ("late_fee_analysis", "Late fee analysis", ("pdf",), "Monthly", "month"),
            ("gateway_settlement", "Gateway settlement", ("excel",), "Weekly", "month"),
            ("programme_collection", "Programme-wise collection", ("pdf", "excel"), "Monthly", "year"),
            ("invoice_register", "Invoice register", ("excel",), "Monthly", "month"),
            ("fee_structure_snapshot", "Fee structure snapshot", ("pdf",), "Quarterly", "year"),
            ("refund_aging", "Refund ageing", ("pdf",), "Weekly", "month"),
            ("scholarship_eligibility", "Scholarship eligibility", ("excel",), "Quarterly", "year"),
            ("audit_trail_finance", "Finance audit trail", ("pdf",), "Monthly", "month"),
        ),
    ),
    "library": _rows(
        (
            ("circulation_summary", "Circulation summary", ("pdf", "excel"), "Monthly", "month"),
            ("overdue_list", "Overdue list", ("csv",), "Daily", "on_demand"),
            ("acquisition_status", "Acquisition status", ("excel",), "Monthly", "year"),
            ("digital_usage", "Digital usage", ("excel",), "Monthly", "year"),
            ("member_activity", "Member activity", ("excel",), "Weekly", "month"),
            ("fine_summary", "Fine summary", ("pdf",), "Monthly", "month"),
            ("reservation_queue", "Reservation queue", ("excel",), "Weekly", "month"),
            ("catalogue_snapshot", "Catalogue snapshot", ("pdf",), "Quarterly", "year"),
            ("branch_inventory", "Branch inventory", ("excel",), "Monthly", "month"),
            ("lost_damaged", "Lost and damaged copies", ("pdf",), "Monthly", "month"),
            ("popular_titles", "Popular titles", ("excel",), "Monthly", "month"),
            ("new_acquisitions", "New acquisitions", ("pdf", "excel"), "Monthly", "month"),
            ("digital_licence_usage", "Digital licence usage", ("excel",), "Monthly", "year"),
            ("membership_status", "Membership status", ("pdf",), "Weekly", "month"),
            ("circulation_by_department", "Circulation by department", ("excel",), "Monthly", "month"),
            ("procurement_pipeline", "Procurement pipeline", ("excel",), "Weekly", "month"),
        ),
    ),
    "hostel": _rows(
        (
            ("occupancy_overview", "Occupancy", ("pdf", "excel"), "Monthly", "month"),
            ("mess_billing_outstanding", "Fee collection", ("excel",), "Weekly", "year"),
            ("maintenance_complaints", "Complaints summary", ("pdf",), "Monthly", "month"),
            ("visitor_log", "Visitor log", ("csv",), "Daily", "month"),
            ("residents_current", "Residents register", ("excel",), "Weekly", "year"),
            ("applications_summary", "Applications summary", ("pdf",), "Monthly", "year"),
            ("mess_enrollment", "Mess enrollment", ("excel",), "Monthly", "month"),
            ("outpass_register", "Outpass register", ("pdf",), "Weekly", "month"),
            ("incidents_summary", "Incidents summary", ("pdf",), "Monthly", "month"),
            ("room_allocation", "Room allocation", ("excel",), "On demand", "year"),
            ("fee_defaulters", "Fee defaulters", ("excel",), "Weekly", "month"),
            ("maintenance_sla", "Maintenance SLA", ("pdf",), "Monthly", "month"),
            ("visitor_compliance", "Visitor compliance", ("csv",), "Daily", "month"),
            ("bed_inventory", "Bed inventory", ("excel",), "Monthly", "year"),
            ("rule_acknowledgements", "Rule acknowledgements", ("pdf",), "Quarterly", "year"),
            ("billing_reconciliation", "Billing reconciliation", ("excel",), "Monthly", "month"),
        ),
    ),
}


def page_rows(page_key: str) -> tuple[ReportsAcademicSeedRow, ...]:
    return _PAGE_ROWS.get(page_key, ())