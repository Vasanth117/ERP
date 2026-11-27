"""Academic reports module catalog (CA 16.02–06)."""

from __future__ import annotations

from dataclasses import dataclass

from app.authorization.permissions import Permission


@dataclass(frozen=True)
class ReportsAcademicPageMeta:
    page_key: str
    page_title: str
    page_subtitle: str
    run_report_key: str
    permission: Permission


@dataclass(frozen=True)
class ReportsAcademicSeedRow:
    report_key: str
    title: str
    export_formats: tuple[str, ...]
    schedule_label: str
    period_kind: str  # month | year | term | on_demand


_PAGE_META: dict[str, ReportsAcademicPageMeta] = {
    "student": ReportsAcademicPageMeta(
        "student",
        "Student Reports",
        "Strength, admissions and status",
        "enrollment",
        Permission.STUDENT_ADMIN_READ,
    ),
    "department": ReportsAcademicPageMeta(
        "department",
        "Department Reports",
        "Department comparisons",
        "dashboard",
        Permission.COLLEGE_DASHBOARD_READ,
    ),
    "academic-performance": ReportsAcademicPageMeta(
        "academic-performance",
        "Academic Performance Reports",
        "Pass percentage and grade distribution",
        "examination",
        Permission.EXAMINATION_ADMIN_READ,
    ),
    "attendance": ReportsAcademicPageMeta(
        "attendance",
        "Attendance Reports",
        "Student and faculty attendance",
        "attendance",
        Permission.ATTENDANCE_ADMIN_READ,
    ),
    "examination": ReportsAcademicPageMeta(
        "examination",
        "Examination Reports",
        "Registration, hall and results",
        "examination",
        Permission.EXAMINATION_ADMIN_READ,
    ),
}


def _rows(
    specs: tuple[tuple[str, str, tuple[str, ...], str, str], ...],
) -> tuple[ReportsAcademicSeedRow, ...]:
    return tuple(
        ReportsAcademicSeedRow(report_key=key, title=title, export_formats=fmts, schedule_label=sched, period_kind=pk)
        for key, title, fmts, sched, pk in specs
    )


_PAGE_ROWS: dict[str, tuple[ReportsAcademicSeedRow, ...]] = {
    "student": _rows(
        (
            ("student_strength", "Student strength", ("pdf", "excel"), "Monthly", "month"),
            ("admissions_summary", "Admissions summary", ("excel",), "Monthly", "year"),
            ("dropouts_transfers", "Dropouts and transfers", ("pdf",), "Quarterly", "year"),
            ("section_occupancy", "Section occupancy", ("excel",), "On demand", "month"),
            ("batch_wise", "Batch-wise strength", ("excel", "pdf"), "Monthly", "year"),
            ("programme_enrolment", "Programme enrolment", ("excel",), "Monthly", "year"),
            ("gender_ratio", "Gender ratio analysis", ("pdf",), "Quarterly", "year"),
            ("hostel_resident_students", "Hostel resident students", ("excel",), "Monthly", "month"),
            ("scholarship_recipients", "Scholarship recipients", ("pdf", "excel"), "Quarterly", "year"),
            ("id_card_status", "ID card issuance status", ("pdf",), "On demand", "month"),
            ("parent_contacts", "Parent contact directory", ("csv",), "On demand", "year"),
            ("alumni_pipeline", "Alumni pipeline", ("excel",), "Monthly", "year"),
            ("transfer_audit", "Transfer audit", ("pdf",), "Quarterly", "year"),
            ("dropout_analysis", "Dropout analysis", ("excel",), "Monthly", "year"),
            ("new_admissions_trend", "New admissions trend", ("excel",), "Weekly", "year"),
            ("registration_completion", "Registration completion", ("pdf",), "Monthly", "term"),
        ),
    ),
    "department": _rows(
        (
            ("department_scorecard", "Department scorecard", ("pdf",), "Monthly", "term"),
            ("programme_enrolment", "Programme enrolment", ("excel",), "Monthly", "year"),
            ("hod_action_summary", "HOD action summary", ("pdf",), "Weekly", "month"),
            ("faculty_student_ratio", "Faculty student ratio", ("excel",), "Monthly", "year"),
            ("resource_utilization", "Resource utilization", ("pdf",), "Monthly", "term"),
            ("cross_dept_comparison", "Cross-department comparison", ("pdf", "excel"), "Quarterly", "term"),
            ("lab_usage", "Lab usage summary", ("excel",), "Monthly", "month"),
            ("budget_vs_actual", "Budget vs actual", ("excel",), "Monthly", "year"),
            ("research_output", "Research output", ("pdf",), "Quarterly", "year"),
            ("accreditation_snapshot", "Accreditation snapshot", ("pdf",), "On demand", "year"),
            ("timetable_compliance", "Timetable compliance", ("excel",), "Weekly", "month"),
            ("infrastructure_gaps", "Infrastructure gaps", ("pdf",), "Quarterly", "year"),
        ),
    ),
    "academic-performance": _rows(
        (
            ("pass_percentage", "Pass percentage", ("pdf", "excel"), "On demand", "term"),
            ("grade_distribution", "Grade distribution", ("excel",), "On demand", "term"),
            ("toppers_list", "Toppers list", ("pdf",), "On demand", "term"),
            ("backlog_analysis", "Backlog analysis", ("excel",), "Monthly", "term"),
            ("cgpa_distribution", "CGPA distribution", ("excel",), "Monthly", "term"),
            ("programme_pass_rates", "Programme pass rates", ("pdf",), "Monthly", "term"),
            ("subject_difficulty", "Subject difficulty index", ("excel",), "Quarterly", "term"),
            ("arrears_register", "Arrears register", ("excel",), "Weekly", "term"),
            ("distinction_holders", "Distinction holders", ("pdf",), "On demand", "term"),
            ("improvement_trackers", "Improvement trackers", ("excel",), "Monthly", "term"),
            ("assessment_outcomes", "Assessment outcomes", ("pdf", "excel"), "Monthly", "term"),
            ("moderation_audit", "Moderation audit", ("pdf",), "Quarterly", "term"),
            ("semester_compare", "Semester comparison", ("excel",), "On demand", "term"),
            ("risk_students", "At-risk students", ("excel",), "Weekly", "term"),
            ("faculty_wise_results", "Faculty-wise results", ("pdf",), "Monthly", "term"),
            ("regulation_impact", "Regulation impact", ("pdf",), "Quarterly", "year"),
        ),
    ),
    "attendance": _rows(
        (
            ("below_threshold", "Below 75%", ("excel",), "Daily", "month"),
            ("subject_wise", "Subject-wise attendance", ("excel",), "Weekly", "month"),
            ("faculty_attendance", "Faculty attendance", ("pdf",), "Daily", "month"),
            ("correction_audit", "Correction audit", ("pdf",), "Monthly", "month"),
            ("department_compliance", "Department compliance", ("excel",), "Weekly", "month"),
            ("daily_digest", "Daily digest", ("pdf",), "Daily", "month"),
            ("session_history", "Session history", ("excel",), "Weekly", "month"),
            ("shortage_notices", "Shortage notices", ("pdf", "csv"), "On demand", "term"),
            ("holiday_impact", "Holiday impact", ("pdf",), "Monthly", "month"),
            ("lab_practical", "Lab / practical attendance", ("excel",), "Weekly", "month"),
            ("monthly_summary", "Monthly summary", ("pdf", "excel"), "Monthly", "month"),
            ("monitoring_exceptions", "Monitoring exceptions", ("excel",), "Daily", "month"),
            ("correction_pending", "Pending corrections", ("pdf",), "Daily", "month"),
            ("faculty_substitution", "Faculty substitution log", ("excel",), "Weekly", "month"),
            ("student_leave_overlap", "Leave overlap report", ("excel",), "Monthly", "month"),
            ("board_prep_sessions", "Board prep sessions", ("pdf",), "On demand", "term"),
        ),
    ),
    "examination": _rows(
        (
            ("exam_registration", "Exam registration", ("excel",), "Weekly", "term"),
            ("hall_allocation", "Hall allocation", ("pdf",), "On demand", "term"),
            ("result_analysis", "Result analysis", ("pdf",), "On demand", "term"),
            ("revaluation_summary", "Revaluation summary", ("excel",), "On demand", "term"),
            ("supplementary_registrations", "Supplementary registrations", ("excel",), "Weekly", "term"),
            ("invigilation_duties", "Invigilation duties", ("pdf",), "On demand", "term"),
            ("seating_plan", "Seating plan export", ("pdf",), "On demand", "term"),
            ("malpractice_cases", "Malpractice cases", ("pdf",), "Monthly", "term"),
            ("question_paper_log", "Question paper log", ("excel",), "Monthly", "term"),
            ("evaluation_status", "Evaluation status", ("excel",), "Daily", "term"),
            ("grade_moderation", "Grade moderation", ("pdf",), "On demand", "term"),
            ("result_publication", "Result publication", ("pdf",), "On demand", "term"),
            ("revaluation_requests", "Revaluation requests", ("excel",), "Weekly", "term"),
            ("supplementary_schedule", "Supplementary schedule", ("pdf",), "On demand", "term"),
            ("eligibility_exceptions", "Eligibility exceptions", ("excel",), "Weekly", "term"),
            ("hall_ticket_status", "Hall ticket status", ("pdf", "excel"), "Daily", "term"),
        ),
    ),
}


def page_meta(page_key: str) -> ReportsAcademicPageMeta | None:
    return _PAGE_META.get(page_key)


def page_rows(page_key: str) -> tuple[ReportsAcademicSeedRow, ...]:
    return _PAGE_ROWS.get(page_key, ())


def all_page_keys() -> tuple[str, ...]:
    return tuple(_PAGE_META.keys())