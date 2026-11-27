"""LMS report catalogue for college admin (CA 15.11)."""

from __future__ import annotations

from dataclasses import dataclass

from app.modules.college_admin.lms_admin_models import LmsScheduledReportFrequency


@dataclass(frozen=True)
class LmsReportCatalogItem:
    report_key: str
    title: str
    export_formats: tuple[str, ...]
    schedule_label: str


_CATALOG: tuple[LmsReportCatalogItem, ...] = (
    LmsReportCatalogItem(
        "course_completion",
        "Course completion",
        ("pdf", "excel"),
        "Weekly",
    ),
    LmsReportCatalogItem(
        "content_usage",
        "Content usage",
        ("excel",),
        "Monthly",
    ),
    LmsReportCatalogItem(
        "assignment_submissions",
        "Assignment submissions",
        ("csv",),
        "Weekly",
    ),
    LmsReportCatalogItem(
        "quiz_performance",
        "Quiz performance",
        ("pdf", "excel"),
        "Monthly",
    ),
    LmsReportCatalogItem(
        "video_engagement",
        "Video engagement",
        ("excel",),
        "Monthly",
    ),
    LmsReportCatalogItem(
        "faculty_upload_activity",
        "Faculty upload activity",
        ("csv", "excel"),
        "Weekly",
    ),
    LmsReportCatalogItem(
        "learner_progress_summary",
        "Learner progress summary",
        ("pdf",),
        "Monthly",
    ),
    LmsReportCatalogItem(
        "assessment_outcomes",
        "Assessment outcomes",
        ("pdf", "excel"),
        "Quarterly",
    ),
    LmsReportCatalogItem(
        "content_review_queue",
        "Content review queue",
        ("csv",),
        "Weekly",
    ),
)

_FREQUENCY_BY_SCHEDULE: dict[str, LmsScheduledReportFrequency] = {
    "Weekly": LmsScheduledReportFrequency.WEEKLY,
    "Monthly": LmsScheduledReportFrequency.MONTHLY,
    "Quarterly": LmsScheduledReportFrequency.QUARTERLY,
}


def catalog_items() -> tuple[LmsReportCatalogItem, ...]:
    return _CATALOG


def catalog_item(report_key: str) -> LmsReportCatalogItem | None:
    key = (report_key or "").strip().lower()
    for item in _CATALOG:
        if item.report_key == key:
            return item
    return None


def default_frequency_for(item: LmsReportCatalogItem) -> LmsScheduledReportFrequency:
    return _FREQUENCY_BY_SCHEDULE.get(item.schedule_label, LmsScheduledReportFrequency.MONTHLY)