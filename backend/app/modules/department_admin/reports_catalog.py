"""Department report catalogue (metadata only)."""

from app.authorization.permissions import Permission
from app.modules.department_admin.phase8_schemas import ReportCatalogItem


REPORT_CATALOG: list[ReportCatalogItem] = [
    ReportCatalogItem(
        report_type="faculty_workload",
        name="Faculty workload",
        description="Faculty assignment counts and workload warnings for the department term.",
        category="faculty",
        supported_formats=["json", "csv"],
        required_permission=Permission.DEPARTMENT_FACULTY_READ.value,
        filter_fields=["academic_year_label", "semester_label", "programme_code", "faculty_user_id"],
    ),
    ReportCatalogItem(
        report_type="student_enrollment",
        name="Student enrollment",
        description="Programme, batch, and section enrollment distribution.",
        category="students",
        supported_formats=["json", "csv"],
        required_permission=Permission.DEPARTMENT_STUDENT_READ.value,
        filter_fields=["academic_year_label", "semester_label", "programme_code", "batch_label", "section_code"],
    ),
    ReportCatalogItem(
        report_type="attendance",
        name="Attendance summary",
        description="Department attendance overview, shortages, and faculty submission signals.",
        category="attendance",
        supported_formats=["json", "csv"],
        required_permission=Permission.DEPARTMENT_ATTENDANCE_READ.value,
        filter_fields=["academic_year_label", "semester_label", "programme_code", "batch_label", "section_code", "date_from", "date_to"],
    ),
    ReportCatalogItem(
        report_type="academic_performance",
        name="Academic performance",
        description="Pass/fail, arrears, and progression aggregates (read-only).",
        category="performance",
        supported_formats=["json", "csv"],
        required_permission=Permission.DEPARTMENT_PERFORMANCE_READ.value,
        filter_fields=["academic_year_label", "semester_label", "programme_code", "batch_label", "section_code", "course_code"],
    ),
    ReportCatalogItem(
        report_type="timetable",
        name="Timetable utilization",
        description="Published timetable and department plan slot summary.",
        category="timetable",
        supported_formats=["json", "csv"],
        required_permission=Permission.DEPARTMENT_TIMETABLE_READ.value,
        filter_fields=["academic_year_label", "semester_label", "programme_code", "batch_label"],
    ),
    ReportCatalogItem(
        report_type="examination_readiness",
        name="Examination readiness",
        description="Assessment completion, marks submission, and readiness indicators.",
        category="examination",
        supported_formats=["json", "csv"],
        required_permission=Permission.DEPARTMENT_ASSESSMENT_READ.value,
        filter_fields=["academic_year_label", "semester_label", "programme_code", "batch_label", "section_code", "course_code"],
    ),
    ReportCatalogItem(
        report_type="operations",
        name="Department operations",
        description="Pending requests, resource utilization, and coordination counts.",
        category="operations",
        supported_formats=["json", "csv"],
        required_permission=Permission.DEPARTMENT_REQUESTS_READ.value,
        filter_fields=["date_from", "date_to"],
    ),
]