"""Permission codes and role-to-permission mapping."""

from enum import Enum

from app.common.roles import Role


class Permission(str, Enum):
  PLATFORM_DASHBOARD_READ = "platform:dashboard:read"
  PLATFORM_TENANT_MANAGE = "platform:tenant:manage"
  PLATFORM_TENANT_READ = "platform:tenant:read"
  PLATFORM_TENANT_LIFECYCLE_MANAGE = "platform:tenant:lifecycle:manage"
  PLATFORM_TENANT_LIFECYCLE_READ = "platform:tenant:lifecycle:read"
  PLATFORM_CONFIG_MANAGE = "platform:config:manage"
  PLATFORM_CONFIG_READ = "platform:config:read"
  TENANT_CONFIG_MANAGE = "tenant:config:manage"
  TENANT_CONFIG_READ = "tenant:config:read"
  TENANT_READ = "tenant:read"
  TENANT_DEPARTMENT_MANAGE = "tenant:department:manage"
  TENANT_DEPARTMENT_READ = "tenant:department:read"
  TENANT_USER_MANAGE = "tenant:user:manage"
  TENANT_USER_READ = "tenant:user:read"
  TENANT_AUDIT_READ = "tenant:audit:read"
  COLLEGE_DASHBOARD_READ = "college:dashboard:read"
  INSTITUTION_PROFILE_READ = "college:institution:read"
  INSTITUTION_PROFILE_MANAGE = "college:institution:manage"
  INSTITUTION_CAMPUS_MANAGE = "college:campus:manage"
  INSTITUTION_SETTINGS_READ = "college:settings:read"
  INSTITUTION_SETTINGS_MANAGE = "college:settings:manage"
  INSTITUTION_USER_READ = "college:user:read"
  INSTITUTION_USER_MANAGE = "college:user:manage"
  INSTITUTION_ROLE_READ = "college:role:read"
  INSTITUTION_ROLE_MANAGE = "college:role:manage"
  INSTITUTION_ORG_READ = "college:organization:read"
  INSTITUTION_ORG_MANAGE = "college:organization:manage"
  INSTITUTION_PRIVILEGED_ROLE_ASSIGN = "college:user:privileged_assign"
  ACADEMIC_CONFIG_READ = "college:academic:read"
  ACADEMIC_CONFIG_MANAGE = "college:academic:manage"
  STUDENT_ADMIN_READ = "college:student_admin:read"
  STUDENT_ADMIN_MANAGE = "college:student_admin:manage"
  FACULTY_ADMIN_READ = "college:faculty_admin:read"
  FACULTY_ADMIN_MANAGE = "college:faculty_admin:manage"
  ATTENDANCE_ADMIN_READ = "college:attendance_admin:read"
  ATTENDANCE_ADMIN_MANAGE = "college:attendance_admin:manage"
  EXAMINATION_ADMIN_READ = "college:examination:read"
  EXAMINATION_ADMIN_CONFIG = "college:examination:config"
  EXAMINATION_ADMIN_MARKS = "college:examination:marks"
  EXAMINATION_ADMIN_PUBLISH = "college:examination:publish"
  FINANCE_ADMIN_READ = "college:finance:read"
  FINANCE_ADMIN_CONFIG = "college:finance:config"
  FINANCE_ADMIN_MANAGE = "college:finance:manage"
  FINANCE_ADMIN_TRANSACTIONS = "college:finance:transactions"
  FINANCE_ADMIN_RECONCILE = "college:finance:reconcile"
  FINANCE_ADMIN_APPROVE = "college:finance:approve"
  HR_ADMIN_READ = "college:hr:read"
  HR_ADMIN_MANAGE = "college:hr:manage"
  HR_ADMIN_LEAVE_APPROVE = "college:hr:leave_approve"
  HR_ADMIN_PAYROLL_CONFIG = "college:hr:payroll_config"
  LIBRARY_ADMIN_READ = "college:library:read"
  LIBRARY_ADMIN_MANAGE = "college:library:manage"
  AUTH_SESSION_MANAGE = "auth:session:manage"
  PLATFORM_USER_MANAGE = "platform:user:manage"
  PLATFORM_USER_READ = "platform:user:read"
  PLATFORM_SECURITY_READ = "platform:security:read"
  PLATFORM_SECURITY_MANAGE = "platform:security:manage"
  PLATFORM_AUDIT_READ = "platform:audit:read"
  PLATFORM_AUDIT_EXPORT = "platform:audit:export"
  SUPPORT_ACCESS_REQUEST = "platform:support:request"
  SUPPORT_ACCESS_APPROVE = "platform:support:approve"
  SUPPORT_ACCESS_EXECUTE = "platform:support:execute"
  PLATFORM_ACCESS_REVIEW_MANAGE = "platform:access_review:manage"
  PLATFORM_OPS_READ = "platform:ops:read"
  PLATFORM_OPS_MANAGE = "platform:ops:manage"
  INTEGRATION_READ = "platform:integration:read"
  INTEGRATION_MANAGE = "platform:integration:manage"
  PLATFORM_EXPORT_READ = "platform:export:read"
  PLATFORM_EXPORT_MANAGE = "platform:export:manage"
  PLATFORM_RETENTION_READ = "platform:retention:read"
  PLATFORM_RETENTION_MANAGE = "platform:retention:manage"
  PLATFORM_OFFBOARDING_MANAGE = "platform:offboarding:manage"
  SUBSCRIPTION_READ = "platform:subscription:read"
  SUBSCRIPTION_MANAGE = "platform:subscription:manage"
  SUBSCRIPTION_BILLING_WEBHOOK = "platform:subscription:webhook"
  FACULTY_SELF_ACCESS = "faculty:self:access"
  FACULTY_PROFILE_READ = "faculty:profile:read"
  FACULTY_PROFILE_UPDATE = "faculty:profile:update"
  FACULTY_DASHBOARD_READ = "faculty:dashboard:read"
  FACULTY_TEACHING_READ = "faculty:teaching:read"
  FACULTY_COURSE_READ = "faculty:course:read"
  FACULTY_COVERAGE_UPDATE = "faculty:coverage:update"
  FACULTY_TIMETABLE_READ = "faculty:timetable:read"
  FACULTY_SESSION_REQUEST = "faculty:session:request"
  FACULTY_ATTENDANCE_READ = "faculty:attendance:read"
  FACULTY_ATTENDANCE_MANAGE = "faculty:attendance:manage"
  FACULTY_LMS_READ = "faculty:lms:read"
  FACULTY_LMS_MANAGE = "faculty:lms:manage"
  FACULTY_ASSESSMENT_READ = "faculty:assessment:read"
  FACULTY_ASSESSMENT_MANAGE = "faculty:assessment:manage"
  FACULTY_MENTORING_READ = "faculty:mentoring:read"
  FACULTY_MENTORING_MANAGE = "faculty:mentoring:manage"
  FACULTY_COMMUNICATION_READ = "faculty:communication:read"
  FACULTY_COMMUNICATION_MANAGE = "faculty:communication:manage"
  FACULTY_SELF_SERVICE_READ = "faculty:self_service:read"
  FACULTY_SELF_SERVICE_MANAGE = "faculty:self_service:manage"
  STUDENT_SELF_ACCESS = "student:self:access"
  STUDENT_PROFILE_READ = "student:profile:read"
  STUDENT_PROFILE_UPDATE = "student:profile:update"
  STUDENT_DASHBOARD_READ = "student:dashboard:read"
  STUDENT_ACADEMIC_READ = "student:academic:read"
  STUDENT_ENROLLMENT_READ = "student:enrollment:read"
  STUDENT_ENROLLMENT_REQUEST = "student:enrollment:request"
  STUDENT_CURRICULUM_READ = "student:curriculum:read"
  STUDENT_REGISTRATION_READ = "student:registration:read"
  STUDENT_REGISTRATION_MANAGE = "student:registration:manage"
  STUDENT_TIMETABLE_READ = "student:timetable:read"
  STUDENT_ATTENDANCE_READ = "student:attendance:read"
  STUDENT_ATTENDANCE_DISCREPANCY = "student:attendance:discrepancy"
  STUDENT_CIA_READ = "student:cia:read"
  STUDENT_CONTINUOUS_ASSESSMENT_READ = "student:continuous_assessment:read"
  STUDENT_PRACTICAL_EXAM_READ = "student:practical_examination:read"
  STUDENT_SEMESTER_EXAM_READ = "student:semester_examination:read"
  STUDENT_EXAM_REGISTRATION_READ = "student:exam_registration:read"
  STUDENT_EXAM_REGISTRATION_MANAGE = "student:exam_registration:manage"
  STUDENT_EXAM_RESULTS_READ = "student:exam_results:read"
  STUDENT_GRADES_READ = "student:grades:read"
  STUDENT_ACADEMIC_DOCUMENTS_READ = "student:academic_documents:read"
  STUDENT_ACADEMIC_DOCUMENTS_REQUEST = "student:academic_documents:request"
  STUDENT_ARREAR_READ = "student:arrear:read"
  STUDENT_ARREAR_MANAGE = "student:arrear:manage"
  STUDENT_EXAM_REVIEW_READ = "student:exam_review:read"
  STUDENT_EXAM_REVIEW_MANAGE = "student:exam_review:manage"
  STUDENT_LMS_READ = "student:lms:read"
  STUDENT_LMS_MANAGE = "student:lms:manage"
  STUDENT_FINANCE_READ = "student:finance:read"
  STUDENT_FINANCE_MANAGE = "student:finance:manage"
  STUDENT_LIBRARY_READ = "student:library:read"
  STUDENT_RESIDENCE_READ = "student:residence:read"
  STUDENT_RESIDENCE_MANAGE = "student:residence:manage"
  STUDENT_SERVICES_READ = "student:services:read"
  STUDENT_SERVICES_MANAGE = "student:services:manage"
  STUDENT_COMMUNICATION_READ = "student:communication:read"
  STUDENT_COMMUNICATION_MANAGE = "student:communication:manage"
  STUDENT_REPORTS_READ = "student:reports:read"
  STUDENT_REPORTS_MANAGE = "student:reports:manage"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
  # Legacy bootstrap account; new operators use platform role assignments (least privilege).
  Role.SUPER_ADMIN: frozenset({Permission.AUTH_SESSION_MANAGE}),
  Role.PLATFORM_ADMIN: frozenset(
    {
      Permission.PLATFORM_DASHBOARD_READ,
      Permission.PLATFORM_TENANT_READ,
      Permission.PLATFORM_TENANT_LIFECYCLE_READ,
      Permission.PLATFORM_CONFIG_READ,
      Permission.TENANT_READ,
      Permission.TENANT_AUDIT_READ,
    }
  ),
  Role.COLLEGE_ADMIN: frozenset(
    {
      Permission.TENANT_READ,
      Permission.TENANT_CONFIG_MANAGE,
      Permission.TENANT_CONFIG_READ,
      Permission.TENANT_DEPARTMENT_MANAGE,
      Permission.TENANT_DEPARTMENT_READ,
      Permission.TENANT_USER_MANAGE,
      Permission.TENANT_USER_READ,
      Permission.TENANT_AUDIT_READ,
      Permission.AUTH_SESSION_MANAGE,
      Permission.COLLEGE_DASHBOARD_READ,
      Permission.INSTITUTION_PROFILE_READ,
      Permission.INSTITUTION_PROFILE_MANAGE,
      Permission.INSTITUTION_CAMPUS_MANAGE,
      Permission.INSTITUTION_SETTINGS_READ,
      Permission.INSTITUTION_SETTINGS_MANAGE,
      Permission.INSTITUTION_USER_READ,
      Permission.INSTITUTION_USER_MANAGE,
      Permission.INSTITUTION_ROLE_READ,
      Permission.INSTITUTION_ROLE_MANAGE,
      Permission.INSTITUTION_ORG_READ,
      Permission.INSTITUTION_ORG_MANAGE,
      Permission.INSTITUTION_PRIVILEGED_ROLE_ASSIGN,
      Permission.ACADEMIC_CONFIG_READ,
      Permission.ACADEMIC_CONFIG_MANAGE,
      Permission.STUDENT_ADMIN_READ,
      Permission.STUDENT_ADMIN_MANAGE,
      Permission.FACULTY_ADMIN_READ,
      Permission.FACULTY_ADMIN_MANAGE,
      Permission.ATTENDANCE_ADMIN_READ,
      Permission.ATTENDANCE_ADMIN_MANAGE,
      Permission.EXAMINATION_ADMIN_READ,
      Permission.EXAMINATION_ADMIN_CONFIG,
      Permission.EXAMINATION_ADMIN_MARKS,
      Permission.EXAMINATION_ADMIN_PUBLISH,
      Permission.FINANCE_ADMIN_READ,
      Permission.FINANCE_ADMIN_CONFIG,
      Permission.FINANCE_ADMIN_MANAGE,
      Permission.FINANCE_ADMIN_TRANSACTIONS,
      Permission.FINANCE_ADMIN_RECONCILE,
      Permission.FINANCE_ADMIN_APPROVE,
      Permission.HR_ADMIN_READ,
      Permission.HR_ADMIN_MANAGE,
      Permission.HR_ADMIN_LEAVE_APPROVE,
      Permission.HR_ADMIN_PAYROLL_CONFIG,
      Permission.LIBRARY_ADMIN_READ,
      Permission.LIBRARY_ADMIN_MANAGE,
    }
  ),
  Role.DEPARTMENT_ADMIN: frozenset(
    {
      Permission.TENANT_READ,
      Permission.TENANT_DEPARTMENT_READ,
      Permission.TENANT_USER_READ,
    }
  ),
  Role.FACULTY: frozenset(
    {
      Permission.TENANT_READ,
      Permission.FACULTY_SELF_ACCESS,
      Permission.FACULTY_PROFILE_READ,
      Permission.FACULTY_PROFILE_UPDATE,
      Permission.FACULTY_DASHBOARD_READ,
      Permission.FACULTY_TEACHING_READ,
      Permission.FACULTY_COURSE_READ,
      Permission.FACULTY_COVERAGE_UPDATE,
      Permission.FACULTY_TIMETABLE_READ,
      Permission.FACULTY_SESSION_REQUEST,
      Permission.FACULTY_ATTENDANCE_READ,
      Permission.FACULTY_ATTENDANCE_MANAGE,
      Permission.FACULTY_LMS_READ,
      Permission.FACULTY_LMS_MANAGE,
      Permission.FACULTY_ASSESSMENT_READ,
      Permission.FACULTY_ASSESSMENT_MANAGE,
      Permission.FACULTY_MENTORING_READ,
      Permission.FACULTY_MENTORING_MANAGE,
      Permission.FACULTY_COMMUNICATION_READ,
      Permission.FACULTY_COMMUNICATION_MANAGE,
      Permission.FACULTY_SELF_SERVICE_READ,
      Permission.FACULTY_SELF_SERVICE_MANAGE,
    }
  ),
  Role.STUDENT: frozenset(
    {
      Permission.TENANT_READ,
      Permission.STUDENT_SELF_ACCESS,
      Permission.STUDENT_PROFILE_READ,
      Permission.STUDENT_PROFILE_UPDATE,
      Permission.STUDENT_DASHBOARD_READ,
      Permission.STUDENT_ACADEMIC_READ,
      Permission.STUDENT_ENROLLMENT_READ,
      Permission.STUDENT_ENROLLMENT_REQUEST,
      Permission.STUDENT_CURRICULUM_READ,
      Permission.STUDENT_REGISTRATION_READ,
      Permission.STUDENT_REGISTRATION_MANAGE,
      Permission.STUDENT_TIMETABLE_READ,
      Permission.STUDENT_ATTENDANCE_READ,
      Permission.STUDENT_ATTENDANCE_DISCREPANCY,
      Permission.STUDENT_CIA_READ,
      Permission.STUDENT_CONTINUOUS_ASSESSMENT_READ,
      Permission.STUDENT_PRACTICAL_EXAM_READ,
      Permission.STUDENT_SEMESTER_EXAM_READ,
      Permission.STUDENT_EXAM_REGISTRATION_READ,
      Permission.STUDENT_EXAM_REGISTRATION_MANAGE,
      Permission.STUDENT_EXAM_RESULTS_READ,
      Permission.STUDENT_GRADES_READ,
      Permission.STUDENT_ACADEMIC_DOCUMENTS_READ,
      Permission.STUDENT_ACADEMIC_DOCUMENTS_REQUEST,
      Permission.STUDENT_ARREAR_READ,
      Permission.STUDENT_ARREAR_MANAGE,
      Permission.STUDENT_EXAM_REVIEW_READ,
      Permission.STUDENT_EXAM_REVIEW_MANAGE,
      Permission.STUDENT_LMS_READ,
      Permission.STUDENT_LMS_MANAGE,
      Permission.STUDENT_FINANCE_READ,
      Permission.STUDENT_FINANCE_MANAGE,
      Permission.STUDENT_LIBRARY_READ,
      Permission.STUDENT_RESIDENCE_READ,
      Permission.STUDENT_RESIDENCE_MANAGE,
      Permission.STUDENT_SERVICES_READ,
      Permission.STUDENT_SERVICES_MANAGE,
      Permission.STUDENT_COMMUNICATION_READ,
      Permission.STUDENT_COMMUNICATION_MANAGE,
      Permission.STUDENT_REPORTS_READ,
      Permission.STUDENT_REPORTS_MANAGE,
    }
  ),
  Role.PARENT: frozenset({Permission.TENANT_READ}),
  Role.FINANCE_STAFF: frozenset({Permission.TENANT_READ, Permission.TENANT_AUDIT_READ}),
  Role.HR_STAFF: frozenset({Permission.TENANT_USER_READ}),
  Role.EXAMINATION_CELL: frozenset({Permission.TENANT_READ, Permission.TENANT_AUDIT_READ}),
  Role.HOSTEL_ADMIN: frozenset({Permission.TENANT_READ}),
  Role.LIBRARIAN: frozenset({Permission.TENANT_READ}),
  Role.ACCOUNTS_STAFF: frozenset({Permission.TENANT_READ, Permission.TENANT_AUDIT_READ}),
}


def permissions_for_role(role: Role) -> frozenset[Permission]:
  return ROLE_PERMISSIONS.get(role, frozenset())
