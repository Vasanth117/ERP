"""Department Admin phase 8 — unit tests (no Mongo)."""

from app.authorization.permissions import Permission, permissions_for_role
from app.common.roles import Role
from app.modules.department_admin.csv_safe import rows_to_csv, sanitize_csv_cell
from app.modules.department_admin.import_export_templates import IMPORT_TEMPLATES
from app.modules.department_admin.reports_catalog import REPORT_CATALOG


def test_department_admin_phase8_permissions():
    perms = permissions_for_role(Role.DEPARTMENT_ADMIN)
    assert Permission.DEPARTMENT_REPORTS_READ in perms
    assert Permission.DEPARTMENT_REPORTS_GENERATE in perms
    assert Permission.DEPARTMENT_DATA_TRANSFER_READ in perms
    assert Permission.DEPARTMENT_DATA_TRANSFER_MANAGE in perms


def test_report_catalog_non_empty():
    assert len(REPORT_CATALOG) >= 7
    types = {r.report_type for r in REPORT_CATALOG}
    assert "attendance" in types
    assert "academic_performance" in types


def test_csv_formula_injection_sanitized():
    assert rows_to_csv([{"name": "=1+1"}], ["name"]).startswith("name")
    assert sanitize_csv_cell("=cmd") == "'=cmd"


def test_import_template_allowlist():
    tpl = IMPORT_TEMPLATES["faculty_course_assignment_rows"]
    assert "faculty_email" in tpl.required_columns
    assert tpl.max_rows <= 5000