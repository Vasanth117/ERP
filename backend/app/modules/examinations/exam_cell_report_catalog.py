"""Examination analytics report catalogue (in-code definitions)."""

from app.modules.examinations.exam_cell_report_schemas import ExamReportCatalogItem

EXAM_REPORT_CATALOG: list[ExamReportCatalogItem] = [
    ExamReportCatalogItem(
        report_type="session_summary",
        name="Examination session summary",
        description="Counts of sessions by status and type for the filter window.",
        category="sessions",
        supported_formats=["json", "csv"],
    ),
    ExamReportCatalogItem(
        report_type="registration_statistics",
        name="Registration statistics",
        description="Registrations by status and confirmation counts.",
        category="registration",
        supported_formats=["json", "csv"],
    ),
    ExamReportCatalogItem(
        report_type="eligibility_statistics",
        name="Eligibility statistics",
        description="Eligible vs ineligible students per session.",
        category="registration",
        supported_formats=["json", "csv"],
    ),
    ExamReportCatalogItem(
        report_type="subject_candidate_counts",
        name="Subject-wise candidate counts",
        description="Registered candidates grouped by course.",
        category="registration",
        supported_formats=["json", "csv"],
    ),
    ExamReportCatalogItem(
        report_type="hall_ticket_statistics",
        name="Hall ticket generation",
        description="Hall tickets issued vs pending.",
        category="operations",
        supported_formats=["json", "csv"],
    ),
    ExamReportCatalogItem(
        report_type="marks_entry_completion",
        name="Marks entry completion",
        description="Approved vs pending marks submissions.",
        category="marks",
        supported_formats=["json", "csv"],
    ),
    ExamReportCatalogItem(
        report_type="pass_fail_by_subject",
        name="Pass / fail by subject",
        description="Outcomes grouped by course code.",
        category="results",
        supported_formats=["json", "csv"],
    ),
    ExamReportCatalogItem(
        report_type="grade_distribution",
        name="Grade distribution",
        description="Frequency of grade letters.",
        category="results",
        supported_formats=["json", "csv"],
    ),
    ExamReportCatalogItem(
        report_type="gpa_distribution",
        name="GPA distribution",
        description="Histogram buckets of semester GPA.",
        category="results",
        supported_formats=["json", "csv"],
    ),
    ExamReportCatalogItem(
        report_type="publication_status",
        name="Result publication status",
        description="Publications by lifecycle state.",
        category="publication",
        supported_formats=["json", "csv"],
    ),
    ExamReportCatalogItem(
        report_type="arrear_supplementary",
        name="Arrear and supplementary",
        description="Pending arrear courses and supplementary registrations.",
        category="supplementary",
        supported_formats=["json", "csv"],
    ),
    ExamReportCatalogItem(
        report_type="revaluation_statistics",
        name="Revaluation applications",
        description="Applications grouped by status and type.",
        category="revaluation",
        supported_formats=["json", "csv"],
    ),
    ExamReportCatalogItem(
        report_type="incident_summary",
        name="Malpractice and incidents",
        description="Incidents and cases by status (restricted fields omitted).",
        category="compliance",
        supported_formats=["json", "csv"],
        sensitive=True,
    ),
    ExamReportCatalogItem(
        report_type="department_performance",
        name="Department-wise performance",
        description="Pass rate by department code on subject results.",
        category="results",
        supported_formats=["json", "csv"],
    ),
    ExamReportCatalogItem(
        report_type="processing_turnaround",
        name="Processing turnaround",
        description="Days from exam end to publication.",
        category="operations",
        supported_formats=["json", "csv"],
    ),
]


def catalog_item(report_type: str) -> ExamReportCatalogItem | None:
    for item in EXAM_REPORT_CATALOG:
        if item.report_type == report_type:
            return item
    return None


def catalog_for_scope(*, can_view_sensitive: bool) -> list[ExamReportCatalogItem]:
    if can_view_sensitive:
        return list(EXAM_REPORT_CATALOG)
    return [i for i in EXAM_REPORT_CATALOG if not i.sensitive]