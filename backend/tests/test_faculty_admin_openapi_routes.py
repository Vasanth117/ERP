"""Faculty administration page APIs must be registered (regression for stale-router 404)."""

from app.main import app

_FACULTY_DASHBOARD_PATH = "/api/v1/college-admin/faculty-administration/dashboard/page"


def test_faculty_employee_dashboard_route_registered() -> None:
    paths = app.openapi()["paths"]
    assert _FACULTY_DASHBOARD_PATH in paths, (
        "Faculty dashboard page route missing — restart uvicorn or check faculty_admin_routes imports"
    )
    assert "get" in paths[_FACULTY_DASHBOARD_PATH]