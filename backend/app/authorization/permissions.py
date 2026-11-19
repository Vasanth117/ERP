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
  EXAMINATION_CELL_DASHBOARD_READ = "examination:dashboard:read"
  EXAMINATION_CELL_SESSION_READ = "examination:session:read"
  EXAMINATION_CELL_SESSION_MANAGE = "examination:session:manage"
  EXAMINATION_CELL_ASSESSMENT_READ = "examination:assessment:read"
  EXAMINATION_CELL_ASSESSMENT_MANAGE = "examination:assessment:manage"
  EXAMINATION_CELL_TIMETABLE_READ = "examination:timetable:read"
  EXAMINATION_CELL_TIMETABLE_MANAGE = "examination:timetable:manage"
  EXAMINATION_CELL_TIMETABLE_APPROVE = "examination:timetable:approve"
  EXAMINATION_CELL_TIMETABLE_PUBLISH = "examination:timetable:publish"
  EXAMINATION_CELL_ELIGIBILITY_READ = "examination:eligibility:read"
  EXAMINATION_CELL_ELIGIBILITY_MANAGE = "examination:eligibility:manage"
  EXAMINATION_CELL_REGISTRATION_READ = "examination:registration:read"
  EXAMINATION_CELL_REGISTRATION_MANAGE = "examination:registration:manage"
  EXAMINATION_CELL_HALL_TICKET_READ = "examination:hall_ticket:read"
  EXAMINATION_CELL_HALL_TICKET_MANAGE = "examination:hall_ticket:manage"
  EXAMINATION_CELL_HALL_TICKET_PUBLISH = "examination:hall_ticket:publish"
  EXAMINATION_CELL_SEATING_READ = "examination:seating:read"
  EXAMINATION_CELL_SEATING_MANAGE = "examination:seating:manage"
  EXAMINATION_CELL_SEATING_PUBLISH = "examination:seating:publish"
  EXAMINATION_CELL_MARKS_READ = "examination:marks:read"
  EXAMINATION_CELL_MARKS_ENTER = "examination:marks:enter"
  EXAMINATION_CELL_MARKS_MANAGE = "examination:marks:manage"
  EXAMINATION_CELL_MARKS_MODERATE = "examination:marks:moderate"
  EXAMINATION_CELL_GRADING_READ = "examination:grading:read"
  EXAMINATION_CELL_GRADING_MANAGE = "examination:grading:manage"
  EXAMINATION_CELL_RESULT_REVIEW = "examination:result:review"
  EXAMINATION_CELL_RESULT_APPROVE = "examination:result:approve"
  EXAMINATION_CELL_PUBLICATION_READ = "examination:publication:read"
  EXAMINATION_CELL_PUBLICATION_MANAGE = "examination:publication:manage"
  EXAMINATION_CELL_PUBLICATION_PUBLISH = "examination:publication:publish"
  EXAMINATION_CELL_DOCUMENT_READ = "examination:document:read"
  EXAMINATION_CELL_DOCUMENT_GENERATE = "examination:document:generate"
  EXAMINATION_CELL_REVALUATION_READ = "examination:revaluation:read"
  EXAMINATION_CELL_REVALUATION_MANAGE = "examination:revaluation:manage"
  EXAMINATION_CELL_SUPPLEMENTARY_READ = "examination:supplementary:read"
  EXAMINATION_CELL_SUPPLEMENTARY_MANAGE = "examination:supplementary:manage"
  EXAMINATION_CELL_INCIDENT_READ = "examination:incident:read"
  EXAMINATION_CELL_INCIDENT_MANAGE = "examination:incident:manage"
  EXAMINATION_CELL_INCIDENT_INVESTIGATE = "examination:incident:investigate"
  EXAMINATION_CELL_NOTIFICATION_READ = "examination:notification:read"
  EXAMINATION_CELL_NOTIFICATION_MANAGE = "examination:notification:manage"
  EXAMINATION_CELL_NOTIFICATION_PUBLISH = "examination:notification:publish"
  EXAMINATION_CELL_REPORT_READ = "examination:report:read"
  EXAMINATION_CELL_REPORT_EXPORT = "examination:report:export"
  EXAMINATION_CELL_INTEGRATION_READ = "examination:integration:read"
  EXAMINATION_CELL_INTEGRATION_MANAGE = "examination:integration:manage"
  EXAMINATION_CELL_AUDIT_READ = "examination:audit:read"
  EXAMINATION_CELL_SECURITY_READ = "examination:security:read"
  EXAMINATION_CELL_SECURITY_MANAGE = "examination:security:manage"
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
  LIBRARY_SELF_ACCESS = "library:self:access"
  LIBRARY_DASHBOARD_READ = "library:dashboard:read"
  LIBRARY_FACILITY_READ = "library:facility:read"
  LIBRARY_FACILITY_MANAGE = "library:facility:manage"
  LIBRARY_CATALOGUE_READ = "library:catalogue:read"
  LIBRARY_CATALOGUE_MANAGE = "library:catalogue:manage"
  LIBRARY_INVENTORY_READ = "library:inventory:read"
  LIBRARY_INVENTORY_MANAGE = "library:inventory:manage"
  LIBRARY_MEMBER_READ = "library:member:read"
  LIBRARY_MEMBER_MANAGE = "library:member:manage"
  LIBRARY_CIRCULATION_READ = "library:circulation:read"
  LIBRARY_CIRCULATION_MANAGE = "library:circulation:manage"
  LIBRARY_RESERVATION_READ = "library:reservation:read"
  LIBRARY_RESERVATION_MANAGE = "library:reservation:manage"
  LIBRARY_FINE_READ = "library:fine:read"
  LIBRARY_FINE_MANAGE = "library:fine:manage"
  LIBRARY_FINE_APPROVE = "library:fine:approve"
  LIBRARY_ACQUISITION_READ = "library:acquisition:read"
  LIBRARY_ACQUISITION_MANAGE = "library:acquisition:manage"
  LIBRARY_ACQUISITION_APPROVE = "library:acquisition:approve"
  LIBRARY_ACQUISITION_PROCURE = "library:acquisition:procure"
  LIBRARY_DIGITAL_READ = "library:digital:read"
  LIBRARY_DIGITAL_MANAGE = "library:digital:manage"
  LIBRARY_NOTIFICATION_READ = "library:notification:read"
  LIBRARY_NOTIFICATION_MANAGE = "library:notification:manage"
  LIBRARY_NOTIFICATION_PUBLISH = "library:notification:publish"
  LIBRARY_NOTIFICATION_RUN = "library:notification:run"
  LIBRARY_REPORT_READ = "library:report:read"
  LIBRARY_REPORT_EXPORT = "library:report:export"
  LIBRARY_REPORT_FINANCE = "library:report:finance"
  LIBRARY_SETTINGS_READ = "library:settings:read"
  LIBRARY_SETTINGS_MANAGE = "library:settings:manage"
  LIBRARY_SETTINGS_APPROVE = "library:settings:approve"
  LIBRARY_AUDIT_READ = "library:audit:read"
  LIBRARY_AUDIT_EXPORT = "library:audit:export"
  LIBRARY_INVENTORY_DISCREPANCY_MANAGE = "library:inventory:discrepancy:manage"
  LIBRARY_INVENTORY_APPROVE = "library:inventory:approve"
  HOSTEL_ADMIN_READ = "college:hostel:read"
  HOSTEL_ADMIN_MANAGE = "college:hostel:manage"
  HOSTEL_ADMIN_ALLOCATE = "college:hostel:allocate"
  COMMUNICATION_ADMIN_READ = "college:communication:read"
  COMMUNICATION_ADMIN_MANAGE = "college:communication:manage"
  COMMUNICATION_ADMIN_PUBLISH = "college:communication:publish"
  COMMUNICATION_ADMIN_CONFIG = "college:communication:config"
  LMS_ADMIN_READ = "college:lms:read"
  LMS_ADMIN_MANAGE = "college:lms:manage"
  LMS_ADMIN_CONFIG = "college:lms:config"
  REPORTS_ADMIN_READ = "college:reports:read"
  REPORTS_ADMIN_GENERATE = "college:reports:generate"
  REPORTS_ADMIN_EXPORT = "college:reports:export"
  REPORTS_ADMIN_SCHEDULE = "college:reports:schedule"
  REPORTS_ADMIN_MANAGE = "college:reports:manage"
  WORKFLOW_ADMIN_READ = "college:workflow:read"
  WORKFLOW_ADMIN_MANAGE = "college:workflow:manage"
  WORKFLOW_ADMIN_APPROVE = "college:workflow:approve"
  WORKFLOW_ADMIN_DELEGATE = "college:workflow:delegate"
  SECURITY_ADMIN_READ = "college:security:read"
  SECURITY_ADMIN_MANAGE = "college:security:manage"
  SECURITY_ADMIN_EXPORT = "college:security:export"
  SECURITY_ADMIN_SESSION = "college:security:session"
  IMPORT_ADMIN_READ = "college:import:read"
  IMPORT_ADMIN_MANAGE = "college:import:manage"
  IMPORT_ADMIN_EXECUTE = "college:import:execute"
  IMPORT_ADMIN_APPROVE = "college:import:approve"
  INTEGRATION_ADMIN_READ = "college:integration:read"
  INTEGRATION_ADMIN_MANAGE = "college:integration:manage"
  INTEGRATION_ADMIN_CONFIG = "college:integration:config"
  HELPDESK_ADMIN_READ = "college:helpdesk:read"
  HELPDESK_ADMIN_MANAGE = "college:helpdesk:manage"
  HELPDESK_ADMIN_ASSIGN = "college:helpdesk:assign"
  HELPDESK_ADMIN_INTERNAL = "college:helpdesk:internal"
  FINANCE_EXT_READ = "college:finance_ext:read"
  FINANCE_EXT_MANAGE = "college:finance_ext:manage"
  FINANCE_EXT_APPROVE = "college:finance_ext:approve"
  FINANCE_EXT_BUDGET = "college:finance_ext:budget"
  OPS_EXT_READ = "college:operations_ext:read"
  OPS_EXT_MANAGE = "college:operations_ext:manage"
  OPS_EXT_MAINTENANCE = "college:operations_ext:maintenance"
  OPS_EXT_INVENTORY = "college:operations_ext:inventory"
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
  STUDENT_SECTION_TRANSFER_REQUEST = "student:section_transfer:request"
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
  DEPARTMENT_SELF_ACCESS = "department:self:access"
  DEPARTMENT_DASHBOARD_READ = "department:dashboard:read"
  DEPARTMENT_PROFILE_READ = "department:profile:read"
  DEPARTMENT_PROFILE_UPDATE = "department:profile:update"
  DEPARTMENT_SETTINGS_READ = "department:settings:read"
  DEPARTMENT_SETTINGS_MANAGE = "department:settings:manage"
  DEPARTMENT_ACADEMIC_CONFIG_READ = "department:academic_config:read"
  DEPARTMENT_FACULTY_READ = "department:faculty:read"
  DEPARTMENT_FACULTY_MANAGE = "department:faculty:manage"
  DEPARTMENT_ACADEMIC_READ = "department:academic:read"
  DEPARTMENT_ACADEMIC_MANAGE = "department:academic:manage"
  DEPARTMENT_CLASS_READ = "department:class:read"
  DEPARTMENT_CLASS_MANAGE = "department:class:manage"
  DEPARTMENT_STUDENT_READ = "department:student:read"
  DEPARTMENT_STUDENT_MANAGE = "department:student:manage"
  DEPARTMENT_TIMETABLE_READ = "department:timetable:read"
  DEPARTMENT_TIMETABLE_MANAGE = "department:timetable:manage"
  DEPARTMENT_ATTENDANCE_READ = "department:attendance:read"
  DEPARTMENT_ATTENDANCE_MANAGE = "department:attendance:manage"
  DEPARTMENT_ASSESSMENT_READ = "department:assessment:read"
  DEPARTMENT_ASSESSMENT_MANAGE = "department:assessment:manage"
  DEPARTMENT_ASSESSMENT_MARKS_DETAIL_READ = "department:assessment:marks_detail:read"
  DEPARTMENT_PERFORMANCE_READ = "department:performance:read"
  DEPARTMENT_CALENDAR_READ = "department:calendar:read"
  DEPARTMENT_CALENDAR_MANAGE = "department:calendar:manage"
  DEPARTMENT_COMMUNICATION_READ = "department:communication:read"
  DEPARTMENT_COMMUNICATION_MANAGE = "department:communication:manage"
  DEPARTMENT_REQUESTS_READ = "department:requests:read"
  DEPARTMENT_REQUESTS_MANAGE = "department:requests:manage"
  DEPARTMENT_RESOURCES_READ = "department:resources:read"
  DEPARTMENT_RESOURCES_MANAGE = "department:resources:manage"
  DEPARTMENT_REPORTS_READ = "department:reports:read"
  DEPARTMENT_REPORTS_GENERATE = "department:reports:generate"
  DEPARTMENT_DATA_TRANSFER_READ = "department:data_transfer:read"
  DEPARTMENT_DATA_TRANSFER_MANAGE = "department:data_transfer:manage"
  DEPARTMENT_DOCUMENTS_READ = "department:documents:read"
  DEPARTMENT_DOCUMENTS_MANAGE = "department:documents:manage"
  DEPARTMENT_AUDIT_READ = "department:audit:read"
  DEPARTMENT_AUDIT_EXPORT = "department:audit:export"
  DEPARTMENT_HELPDESK_READ = "department:helpdesk:read"
  DEPARTMENT_HELPDESK_MANAGE = "department:helpdesk:manage"
  DEPARTMENT_PLACEMENT_READ = "department:placement:read"
  DEPARTMENT_PLACEMENT_MANAGE = "department:placement:manage"
  DEPARTMENT_RESEARCH_READ = "department:research:read"
  DEPARTMENT_RESEARCH_MANAGE = "department:research:manage"


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
      Permission.EXAMINATION_CELL_DASHBOARD_READ,
      Permission.EXAMINATION_CELL_SESSION_READ,
      Permission.EXAMINATION_CELL_SESSION_MANAGE,
      Permission.EXAMINATION_CELL_ASSESSMENT_READ,
      Permission.EXAMINATION_CELL_ASSESSMENT_MANAGE,
      Permission.EXAMINATION_CELL_TIMETABLE_READ,
      Permission.EXAMINATION_CELL_TIMETABLE_MANAGE,
      Permission.EXAMINATION_CELL_TIMETABLE_APPROVE,
      Permission.EXAMINATION_CELL_TIMETABLE_PUBLISH,
      Permission.EXAMINATION_CELL_ELIGIBILITY_READ,
      Permission.EXAMINATION_CELL_ELIGIBILITY_MANAGE,
      Permission.EXAMINATION_CELL_REGISTRATION_READ,
      Permission.EXAMINATION_CELL_REGISTRATION_MANAGE,
      Permission.EXAMINATION_CELL_HALL_TICKET_READ,
      Permission.EXAMINATION_CELL_HALL_TICKET_MANAGE,
      Permission.EXAMINATION_CELL_HALL_TICKET_PUBLISH,
      Permission.EXAMINATION_CELL_SEATING_READ,
      Permission.EXAMINATION_CELL_SEATING_MANAGE,
      Permission.EXAMINATION_CELL_SEATING_PUBLISH,
      Permission.EXAMINATION_CELL_MARKS_READ,
      Permission.EXAMINATION_CELL_MARKS_ENTER,
      Permission.EXAMINATION_CELL_MARKS_MANAGE,
      Permission.EXAMINATION_CELL_MARKS_MODERATE,
      Permission.EXAMINATION_CELL_GRADING_READ,
      Permission.EXAMINATION_CELL_GRADING_MANAGE,
      Permission.EXAMINATION_CELL_RESULT_REVIEW,
      Permission.EXAMINATION_CELL_RESULT_APPROVE,
      Permission.EXAMINATION_CELL_PUBLICATION_READ,
      Permission.EXAMINATION_CELL_PUBLICATION_MANAGE,
      Permission.EXAMINATION_CELL_PUBLICATION_PUBLISH,
      Permission.EXAMINATION_CELL_DOCUMENT_READ,
      Permission.EXAMINATION_CELL_DOCUMENT_GENERATE,
      Permission.EXAMINATION_CELL_REVALUATION_READ,
      Permission.EXAMINATION_CELL_REVALUATION_MANAGE,
      Permission.EXAMINATION_CELL_SUPPLEMENTARY_READ,
      Permission.EXAMINATION_CELL_SUPPLEMENTARY_MANAGE,
      Permission.EXAMINATION_CELL_INCIDENT_READ,
      Permission.EXAMINATION_CELL_INCIDENT_MANAGE,
      Permission.EXAMINATION_CELL_INCIDENT_INVESTIGATE,
      Permission.EXAMINATION_CELL_NOTIFICATION_READ,
      Permission.EXAMINATION_CELL_NOTIFICATION_MANAGE,
      Permission.EXAMINATION_CELL_NOTIFICATION_PUBLISH,
      Permission.EXAMINATION_CELL_REPORT_READ,
      Permission.EXAMINATION_CELL_REPORT_EXPORT,
      Permission.EXAMINATION_CELL_INTEGRATION_READ,
      Permission.EXAMINATION_CELL_INTEGRATION_MANAGE,
      Permission.EXAMINATION_CELL_AUDIT_READ,
      Permission.EXAMINATION_CELL_SECURITY_READ,
      Permission.EXAMINATION_CELL_SECURITY_MANAGE,
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
      Permission.LIBRARY_FACILITY_READ,
      Permission.LIBRARY_FACILITY_MANAGE,
      Permission.LIBRARY_CATALOGUE_READ,
      Permission.LIBRARY_CATALOGUE_MANAGE,
      Permission.LIBRARY_INVENTORY_READ,
      Permission.LIBRARY_INVENTORY_MANAGE,
      Permission.LIBRARY_MEMBER_READ,
      Permission.LIBRARY_MEMBER_MANAGE,
      Permission.LIBRARY_CIRCULATION_READ,
      Permission.LIBRARY_CIRCULATION_MANAGE,
      Permission.LIBRARY_RESERVATION_READ,
      Permission.LIBRARY_RESERVATION_MANAGE,
      Permission.LIBRARY_FINE_READ,
      Permission.LIBRARY_FINE_MANAGE,
      Permission.LIBRARY_FINE_APPROVE,
      Permission.LIBRARY_ACQUISITION_READ,
      Permission.LIBRARY_ACQUISITION_MANAGE,
      Permission.LIBRARY_ACQUISITION_APPROVE,
      Permission.LIBRARY_ACQUISITION_PROCURE,
      Permission.LIBRARY_DIGITAL_READ,
      Permission.LIBRARY_DIGITAL_MANAGE,
      Permission.LIBRARY_NOTIFICATION_READ,
      Permission.LIBRARY_NOTIFICATION_MANAGE,
      Permission.LIBRARY_NOTIFICATION_PUBLISH,
      Permission.LIBRARY_NOTIFICATION_RUN,
      Permission.LIBRARY_REPORT_READ,
      Permission.LIBRARY_REPORT_EXPORT,
      Permission.LIBRARY_REPORT_FINANCE,
      Permission.LIBRARY_SETTINGS_READ,
      Permission.LIBRARY_SETTINGS_MANAGE,
      Permission.LIBRARY_SETTINGS_APPROVE,
      Permission.LIBRARY_AUDIT_READ,
      Permission.LIBRARY_AUDIT_EXPORT,
      Permission.LIBRARY_INVENTORY_DISCREPANCY_MANAGE,
      Permission.LIBRARY_INVENTORY_APPROVE,
      Permission.HOSTEL_ADMIN_READ,
      Permission.HOSTEL_ADMIN_MANAGE,
      Permission.HOSTEL_ADMIN_ALLOCATE,
      Permission.COMMUNICATION_ADMIN_READ,
      Permission.COMMUNICATION_ADMIN_MANAGE,
      Permission.COMMUNICATION_ADMIN_PUBLISH,
      Permission.COMMUNICATION_ADMIN_CONFIG,
      Permission.LMS_ADMIN_READ,
      Permission.LMS_ADMIN_MANAGE,
      Permission.LMS_ADMIN_CONFIG,
      Permission.REPORTS_ADMIN_READ,
      Permission.REPORTS_ADMIN_GENERATE,
      Permission.REPORTS_ADMIN_EXPORT,
      Permission.REPORTS_ADMIN_SCHEDULE,
      Permission.REPORTS_ADMIN_MANAGE,
      Permission.WORKFLOW_ADMIN_READ,
      Permission.WORKFLOW_ADMIN_MANAGE,
      Permission.WORKFLOW_ADMIN_APPROVE,
      Permission.WORKFLOW_ADMIN_DELEGATE,
      Permission.SECURITY_ADMIN_READ,
      Permission.SECURITY_ADMIN_MANAGE,
      Permission.SECURITY_ADMIN_EXPORT,
      Permission.SECURITY_ADMIN_SESSION,
      Permission.IMPORT_ADMIN_READ,
      Permission.IMPORT_ADMIN_MANAGE,
      Permission.IMPORT_ADMIN_EXECUTE,
      Permission.IMPORT_ADMIN_APPROVE,
      Permission.INTEGRATION_ADMIN_READ,
      Permission.INTEGRATION_ADMIN_MANAGE,
      Permission.INTEGRATION_ADMIN_CONFIG,
      Permission.HELPDESK_ADMIN_READ,
      Permission.HELPDESK_ADMIN_MANAGE,
      Permission.HELPDESK_ADMIN_ASSIGN,
      Permission.HELPDESK_ADMIN_INTERNAL,
      Permission.FINANCE_EXT_READ,
      Permission.FINANCE_EXT_MANAGE,
      Permission.FINANCE_EXT_APPROVE,
      Permission.FINANCE_EXT_BUDGET,
      Permission.OPS_EXT_READ,
      Permission.OPS_EXT_MANAGE,
      Permission.OPS_EXT_MAINTENANCE,
      Permission.OPS_EXT_INVENTORY,
    }
  ),
  Role.DEPARTMENT_ADMIN: frozenset(
    {
      Permission.TENANT_READ,
      Permission.TENANT_DEPARTMENT_READ,
      Permission.TENANT_USER_READ,
      Permission.DEPARTMENT_SELF_ACCESS,
      Permission.DEPARTMENT_DASHBOARD_READ,
      Permission.DEPARTMENT_PROFILE_READ,
      Permission.DEPARTMENT_PROFILE_UPDATE,
      Permission.DEPARTMENT_SETTINGS_READ,
      Permission.DEPARTMENT_SETTINGS_MANAGE,
      Permission.DEPARTMENT_ACADEMIC_CONFIG_READ,
      Permission.DEPARTMENT_FACULTY_READ,
      Permission.DEPARTMENT_FACULTY_MANAGE,
      Permission.DEPARTMENT_ACADEMIC_READ,
      Permission.DEPARTMENT_ACADEMIC_MANAGE,
      Permission.DEPARTMENT_CLASS_READ,
      Permission.DEPARTMENT_CLASS_MANAGE,
      Permission.DEPARTMENT_STUDENT_READ,
      Permission.DEPARTMENT_STUDENT_MANAGE,
      Permission.DEPARTMENT_TIMETABLE_READ,
      Permission.DEPARTMENT_TIMETABLE_MANAGE,
      Permission.DEPARTMENT_ATTENDANCE_READ,
      Permission.DEPARTMENT_ATTENDANCE_MANAGE,
      Permission.DEPARTMENT_ASSESSMENT_READ,
      Permission.DEPARTMENT_ASSESSMENT_MANAGE,
      Permission.DEPARTMENT_PERFORMANCE_READ,
      Permission.DEPARTMENT_CALENDAR_READ,
      Permission.DEPARTMENT_CALENDAR_MANAGE,
      Permission.DEPARTMENT_COMMUNICATION_READ,
      Permission.DEPARTMENT_COMMUNICATION_MANAGE,
      Permission.DEPARTMENT_REQUESTS_READ,
      Permission.DEPARTMENT_REQUESTS_MANAGE,
      Permission.DEPARTMENT_RESOURCES_READ,
      Permission.DEPARTMENT_RESOURCES_MANAGE,
      Permission.DEPARTMENT_REPORTS_READ,
      Permission.DEPARTMENT_REPORTS_GENERATE,
      Permission.DEPARTMENT_DATA_TRANSFER_READ,
      Permission.DEPARTMENT_DATA_TRANSFER_MANAGE,
      Permission.DEPARTMENT_DOCUMENTS_READ,
      Permission.DEPARTMENT_DOCUMENTS_MANAGE,
      Permission.DEPARTMENT_AUDIT_READ,
      Permission.DEPARTMENT_AUDIT_EXPORT,
      Permission.DEPARTMENT_HELPDESK_READ,
      Permission.DEPARTMENT_HELPDESK_MANAGE,
      Permission.DEPARTMENT_PLACEMENT_READ,
      Permission.DEPARTMENT_PLACEMENT_MANAGE,
      Permission.DEPARTMENT_RESEARCH_READ,
      Permission.DEPARTMENT_RESEARCH_MANAGE,
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
      Permission.STUDENT_SECTION_TRANSFER_REQUEST,
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
      Permission.EXAMINATION_CELL_NOTIFICATION_READ,
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
  Role.EXAMINATION_CELL: frozenset(
    {
      Permission.TENANT_READ,
      Permission.TENANT_AUDIT_READ,
      Permission.EXAMINATION_CELL_DASHBOARD_READ,
      Permission.EXAMINATION_CELL_SESSION_READ,
      Permission.EXAMINATION_CELL_SESSION_MANAGE,
      Permission.EXAMINATION_CELL_ASSESSMENT_READ,
      Permission.EXAMINATION_CELL_ASSESSMENT_MANAGE,
      Permission.EXAMINATION_CELL_TIMETABLE_READ,
      Permission.EXAMINATION_CELL_TIMETABLE_MANAGE,
      Permission.EXAMINATION_CELL_TIMETABLE_APPROVE,
      Permission.EXAMINATION_CELL_TIMETABLE_PUBLISH,
      Permission.EXAMINATION_CELL_ELIGIBILITY_READ,
      Permission.EXAMINATION_CELL_ELIGIBILITY_MANAGE,
      Permission.EXAMINATION_CELL_REGISTRATION_READ,
      Permission.EXAMINATION_CELL_REGISTRATION_MANAGE,
      Permission.EXAMINATION_CELL_HALL_TICKET_READ,
      Permission.EXAMINATION_CELL_HALL_TICKET_MANAGE,
      Permission.EXAMINATION_CELL_HALL_TICKET_PUBLISH,
      Permission.EXAMINATION_CELL_SEATING_READ,
      Permission.EXAMINATION_CELL_SEATING_MANAGE,
      Permission.EXAMINATION_CELL_SEATING_PUBLISH,
      Permission.EXAMINATION_CELL_MARKS_READ,
      Permission.EXAMINATION_CELL_MARKS_ENTER,
      Permission.EXAMINATION_CELL_MARKS_MANAGE,
      Permission.EXAMINATION_CELL_MARKS_MODERATE,
      Permission.EXAMINATION_CELL_GRADING_READ,
      Permission.EXAMINATION_CELL_GRADING_MANAGE,
      Permission.EXAMINATION_CELL_RESULT_REVIEW,
      Permission.EXAMINATION_CELL_RESULT_APPROVE,
      Permission.EXAMINATION_CELL_PUBLICATION_READ,
      Permission.EXAMINATION_CELL_PUBLICATION_MANAGE,
      Permission.EXAMINATION_CELL_PUBLICATION_PUBLISH,
      Permission.EXAMINATION_CELL_DOCUMENT_READ,
      Permission.EXAMINATION_CELL_DOCUMENT_GENERATE,
      Permission.EXAMINATION_CELL_REVALUATION_READ,
      Permission.EXAMINATION_CELL_REVALUATION_MANAGE,
      Permission.EXAMINATION_CELL_SUPPLEMENTARY_READ,
      Permission.EXAMINATION_CELL_SUPPLEMENTARY_MANAGE,
      Permission.EXAMINATION_CELL_INCIDENT_READ,
      Permission.EXAMINATION_CELL_INCIDENT_MANAGE,
      Permission.EXAMINATION_CELL_INCIDENT_INVESTIGATE,
      Permission.EXAMINATION_CELL_NOTIFICATION_READ,
      Permission.EXAMINATION_CELL_NOTIFICATION_MANAGE,
      Permission.EXAMINATION_CELL_NOTIFICATION_PUBLISH,
      Permission.EXAMINATION_CELL_REPORT_READ,
      Permission.EXAMINATION_CELL_REPORT_EXPORT,
      Permission.EXAMINATION_CELL_INTEGRATION_READ,
      Permission.EXAMINATION_CELL_INTEGRATION_MANAGE,
      Permission.EXAMINATION_CELL_AUDIT_READ,
      Permission.EXAMINATION_CELL_SECURITY_READ,
      Permission.EXAMINATION_CELL_SECURITY_MANAGE,
    }
  ),
  Role.HOSTEL_ADMIN: frozenset({Permission.TENANT_READ}),
  Role.LIBRARIAN: frozenset(
    {
      Permission.TENANT_READ,
      Permission.LIBRARY_SELF_ACCESS,
      Permission.LIBRARY_DASHBOARD_READ,
      Permission.LIBRARY_FACILITY_READ,
      Permission.LIBRARY_FACILITY_MANAGE,
      Permission.LIBRARY_CATALOGUE_READ,
      Permission.LIBRARY_CATALOGUE_MANAGE,
      Permission.LIBRARY_INVENTORY_READ,
      Permission.LIBRARY_INVENTORY_MANAGE,
      Permission.LIBRARY_MEMBER_READ,
      Permission.LIBRARY_MEMBER_MANAGE,
      Permission.LIBRARY_CIRCULATION_READ,
      Permission.LIBRARY_CIRCULATION_MANAGE,
      Permission.LIBRARY_RESERVATION_READ,
      Permission.LIBRARY_RESERVATION_MANAGE,
      Permission.LIBRARY_FINE_READ,
      Permission.LIBRARY_FINE_MANAGE,
      Permission.LIBRARY_ACQUISITION_READ,
      Permission.LIBRARY_ACQUISITION_MANAGE,
      Permission.LIBRARY_DIGITAL_READ,
      Permission.LIBRARY_DIGITAL_MANAGE,
      Permission.LIBRARY_NOTIFICATION_READ,
      Permission.LIBRARY_NOTIFICATION_MANAGE,
      Permission.LIBRARY_NOTIFICATION_RUN,
      Permission.LIBRARY_REPORT_READ,
      Permission.LIBRARY_REPORT_EXPORT,
      Permission.LIBRARY_SETTINGS_READ,
      Permission.LIBRARY_SETTINGS_MANAGE,
      Permission.LIBRARY_AUDIT_READ,
      Permission.LIBRARY_AUDIT_EXPORT,
      Permission.LIBRARY_INVENTORY_DISCREPANCY_MANAGE,
    }
  ),
  Role.ACCOUNTS_STAFF: frozenset({Permission.TENANT_READ, Permission.TENANT_AUDIT_READ}),
}


def permissions_for_role(role: Role) -> frozenset[Permission]:
  return ROLE_PERMISSIONS.get(role, frozenset())
