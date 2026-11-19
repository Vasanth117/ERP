/** Read-only GET endpoints per College Admin sidebar module (API integration for generated screens). */
export const moduleApiMap: Record<
  string,
  { label: string; path: string }[]
> = {
  academics: [
    { label: "Academic years", path: "/college-admin/academic-config/years" },
    { label: "Programmes", path: "/college-admin/academic-config/programmes" },
    { label: "Courses", path: "/college-admin/academic-config/courses" },
  ],
  students: [
    { label: "Student registry", path: "/college-admin/student-administration/students" },
    { label: "Enrollment batches", path: "/college-admin/student-administration/enrollments" },
  ],
  faculty: [
    { label: "Faculty registry", path: "/college-admin/faculty-administration/faculty" },
  ],
  attendance: [
    { label: "Policies", path: "/college-admin/attendance-administration/policies" },
    { label: "Sessions", path: "/college-admin/attendance-administration/sessions" },
  ],
  examinations: [
    { label: "Exam sessions", path: "/college-admin/examination-administration/sessions" },
  ],
  finance: [
    { label: "Fee structures", path: "/college-admin/finance-administration/fee-structures" },
  ],
  hr: [{ label: "Staff registry", path: "/college-admin/hr-administration/staff" }],
  library: [
    { label: "Branches", path: "/college-admin/library-administration/branches" },
  ],
  hostel: [
    { label: "Hostels", path: "/college-admin/hostel-administration/hostels" },
  ],
  communication: [
    { label: "Announcements", path: "/college-admin/communication-administration/announcements" },
  ],
  lms: [
    { label: "LMS settings", path: "/college-admin/lms-administration/settings" },
  ],
  reports: [
    { label: "Report definitions", path: "/college-admin/reports-analytics/definitions" },
  ],
  approvals: [
    { label: "Workflow definitions", path: "/college-admin/workflow-administration/definitions" },
  ],
  security: [
    { label: "Audit events", path: "/college-admin/security-administration/audit-events" },
  ],
  "data-import": [
    { label: "Import jobs", path: "/college-admin/data-import/jobs" },
  ],
  integrations: [
    { label: "Integrations", path: "/college-admin/integration-administration/providers" },
  ],
  helpdesk: [
    { label: "Support requests", path: "/college-admin/helpdesk/requests" },
  ],
  "finance-extensions": [
    { label: "Budgets", path: "/college-admin/finance-extensions/budgets" },
  ],
  operations: [
    { label: "Assets", path: "/college-admin/operations-extensions/assets" },
  ],
};