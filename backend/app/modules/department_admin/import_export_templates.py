"""Approved department import/export templates (allowlists only)."""

from __future__ import annotations

from dataclasses import dataclass

from app.authorization.permissions import Permission


@dataclass(frozen=True)
class ImportTemplate:
    template_id: str
    entity_type: str
    version: str
    required_columns: frozenset[str]
    optional_columns: frozenset[str]
    max_rows: int
    permission: Permission
    description: str


@dataclass(frozen=True)
class ExportDataset:
    dataset_id: str
    description: str
    permission: Permission
    allowed_fields: frozenset[str]
    default_fields: frozenset[str]


IMPORT_TEMPLATES: dict[str, ImportTemplate] = {
    "faculty_course_assignment_rows": ImportTemplate(
        template_id="faculty_course_assignment_rows",
        entity_type="faculty_assignment_request",
        version="1",
        required_columns=frozenset({"faculty_email", "course_code", "section", "academic_year_label", "semester_label"}),
        optional_columns=frozenset({"note"}),
        max_rows=2000,
        permission=Permission.DEPARTMENT_FACULTY_MANAGE,
        description="Creates pending faculty course assignment requests (does not change college HR records).",
    ),
}

EXPORT_DATASETS: dict[str, ExportDataset] = {
    "student_directory": ExportDataset(
        dataset_id="student_directory",
        description="Department student directory (allowlisted fields).",
        permission=Permission.DEPARTMENT_STUDENT_READ,
        allowed_fields=frozenset(
            {
                "student_user_id",
                "full_name",
                "email",
                "roll_number",
                "programme_code",
                "batch_label",
                "section_code",
                "enrollment_status",
            }
        ),
        default_fields=frozenset(
            {"roll_number", "full_name", "email", "programme_code", "batch_label", "section_code", "enrollment_status"}
        ),
    ),
    "faculty_directory": ExportDataset(
        dataset_id="faculty_directory",
        description="Department faculty directory.",
        permission=Permission.DEPARTMENT_FACULTY_READ,
        allowed_fields=frozenset(
            {
                "faculty_user_id",
                "full_name",
                "email",
                "employee_id",
                "designation",
                "faculty_code",
            }
        ),
        default_fields=frozenset({"faculty_user_id", "full_name", "email", "designation"}),
    ),
    "faculty_workload_summary": ExportDataset(
        dataset_id="faculty_workload_summary",
        description="Faculty assignment counts for the selected term.",
        permission=Permission.DEPARTMENT_FACULTY_READ,
        allowed_fields=frozenset(
            {"faculty_user_id", "full_name", "assignment_count", "academic_year_label", "semester_label"}
        ),
        default_fields=frozenset({"faculty_user_id", "full_name", "assignment_count"}),
    ),
}