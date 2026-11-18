"""Library report type identifiers."""

from enum import StrEnum


class LibraryReportType(StrEnum):
    OVERVIEW = "overview"
    CATALOGUE = "catalogue_statistics"
    INVENTORY = "physical_inventory"
    CIRCULATION = "circulation_summary"
    OVERDUE = "overdue_books"
    MEMBER_ACTIVITY = "member_activity"
    CIRCULATION_HISTORY = "circulation_history"
    RESERVATIONS = "reservation_statistics"
    FINES = "fine_summary"
    LOST_DAMAGED = "lost_damaged"
    ACQUISITION = "acquisition_procurement"
    DIGITAL_USAGE = "digital_usage"
    BRANCH_PERFORMANCE = "branch_performance"
    POPULAR_BOOKS = "popular_books"