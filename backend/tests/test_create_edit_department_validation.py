import pytest

from app.core.exceptions import AppError
from app.modules.college_admin.create_edit_department_page_service import _validate_form
from app.modules.college_admin.schemas import CreateEditDepartmentFormValues


def test_strict_validation_returns_field_details() -> None:
    form = CreateEditDepartmentFormValues(
        name="",
        department_code="",
        organization_unit_id="",
        campus_id="",
        establishment_year=None,
    )
    with pytest.raises(AppError) as exc_info:
        _validate_form(form, strict=True, school_selectable=0, campus_selectable=1)

    err = exc_info.value
    assert err.code == "VALIDATION_ERROR"
    assert err.details
    org_row = next(row for row in err.details if row["field_key"] == "organization_unit_id")
    assert org_row["action_type"] == "navigate"
    assert org_row["action_href"] == "/college-admin/organization/organizational-hierarchy"