"""Profile completeness rules."""

from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.hr.employee_profile_models import EmergencyContact, HrEmployeeProfile, PostalAddress
from app.modules.hr.enums import ProfileCompletionStatus


_REQUIRED_SCALAR = (
    "first_name",
    "last_name",
    "official_email",
    "mobile_number",
    "date_of_birth",
    "gender",
    "employee_category",
)


def _address_complete(addr: PostalAddress | None) -> bool:
    if addr is None:
        return False
    return bool(addr.line1 and addr.city and addr.state and addr.country)


def _emergency_complete(contact: EmergencyContact | None) -> bool:
    if contact is None:
        return False
    return bool(contact.name and contact.relationship and contact.primary_phone)


def compute_missing_fields(profile: HrEmployeeProfile, employee: EmployeeRecord) -> list[str]:
    missing: list[str] = []
    for field in _REQUIRED_SCALAR:
        if not getattr(profile, field, None):
            missing.append(field)
    if not employee.employee_id:
        missing.append("employee_id")
    if not employee.joining_date:
        missing.append("joining_date")
    if not employee.department_id:
        missing.append("department_id")
    if not employee.designation:
        missing.append("designation")
    if not employee.employment_type:
        missing.append("employment_type")
    if not employee.campus_id:
        missing.append("campus_id")
    if not _address_complete(profile.current_address):
        missing.append("current_address")
    if not profile.addresses_same and not _address_complete(profile.permanent_address):
        missing.append("permanent_address")
    if not _emergency_complete(profile.emergency_contact):
        missing.append("emergency_contact")
    return missing


def apply_completion_status(profile: HrEmployeeProfile, employee: EmployeeRecord) -> None:
    missing = compute_missing_fields(profile, employee)
    profile.missing_fields = missing
    profile.profile_completion_status = (
        ProfileCompletionStatus.COMPLETE if not missing else ProfileCompletionStatus.INCOMPLETE
    )