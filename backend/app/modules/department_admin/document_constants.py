"""Approved departmental document categories (extend via College Admin policy when available)."""

DOCUMENT_CATEGORIES = frozenset(
    {
        "department_administration",
        "academic_curriculum",
        "faculty_coordination",
        "meetings_minutes",
        "seminars_workshops",
        "project_reviews",
        "department_events",
        "resource_records",
        "reports",
        "other",
    }
)