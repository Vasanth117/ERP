"""Permission policy unit tests."""

from app.authorization.permissions import Permission, permissions_for_role
from app.common.roles import Role


def test_college_admin_can_manage_users() -> None:
    perms = permissions_for_role(Role.COLLEGE_ADMIN)
    assert Permission.TENANT_USER_MANAGE in perms
    assert Permission.PLATFORM_TENANT_MANAGE not in perms
    assert Permission.COLLEGE_DASHBOARD_READ in perms
    assert Permission.INSTITUTION_SETTINGS_MANAGE in perms
    assert Permission.INSTITUTION_USER_MANAGE in perms
    assert Permission.INSTITUTION_ORG_MANAGE in perms


def test_student_has_minimal_permissions() -> None:
    perms = permissions_for_role(Role.STUDENT)
    assert Permission.TENANT_USER_MANAGE not in perms
    assert Permission.TENANT_READ in perms


def test_student_portal_permissions_complete() -> None:
    perms = permissions_for_role(Role.STUDENT)
    assert Permission.STUDENT_SELF_ACCESS in perms
    assert Permission.STUDENT_DASHBOARD_READ in perms
    assert Permission.STUDENT_ENROLLMENT_REQUEST in perms
    assert Permission.STUDENT_CURRICULUM_READ in perms
    assert Permission.STUDENT_REGISTRATION_MANAGE in perms
    assert Permission.STUDENT_TIMETABLE_READ in perms
    assert Permission.STUDENT_ATTENDANCE_DISCREPANCY in perms
    assert Permission.STUDENT_CIA_READ in perms
    assert Permission.STUDENT_CONTINUOUS_ASSESSMENT_READ in perms
    assert Permission.STUDENT_PRACTICAL_EXAM_READ in perms
    assert Permission.STUDENT_SEMESTER_EXAM_READ in perms
    assert Permission.STUDENT_EXAM_REGISTRATION_READ in perms
    assert Permission.STUDENT_EXAM_REGISTRATION_MANAGE in perms
    assert Permission.STUDENT_EXAM_RESULTS_READ in perms
    assert Permission.STUDENT_GRADES_READ in perms
    assert Permission.STUDENT_ACADEMIC_DOCUMENTS_READ in perms
    assert Permission.STUDENT_ACADEMIC_DOCUMENTS_REQUEST in perms
    assert Permission.STUDENT_ARREAR_READ in perms
    assert Permission.STUDENT_ARREAR_MANAGE in perms
    assert Permission.STUDENT_EXAM_REVIEW_READ in perms
    assert Permission.STUDENT_EXAM_REVIEW_MANAGE in perms
    assert Permission.STUDENT_LMS_READ in perms
    assert Permission.STUDENT_LMS_MANAGE in perms
    assert Permission.STUDENT_FINANCE_READ in perms
    assert Permission.STUDENT_FINANCE_MANAGE in perms
    assert Permission.STUDENT_LIBRARY_READ in perms
    assert Permission.STUDENT_RESIDENCE_READ in perms
    assert Permission.STUDENT_SERVICES_MANAGE in perms
    assert Permission.STUDENT_COMMUNICATION_READ in perms
    assert Permission.STUDENT_REPORTS_MANAGE in perms
    assert Permission.FACULTY_SELF_ACCESS not in perms


def test_faculty_portal_permissions_complete() -> None:
    perms = permissions_for_role(Role.FACULTY)
    assert Permission.FACULTY_SELF_ACCESS in perms
    assert Permission.FACULTY_COMMUNICATION_MANAGE in perms
    assert Permission.FACULTY_SELF_SERVICE_MANAGE in perms
    assert Permission.FACULTY_ASSESSMENT_MANAGE in perms
