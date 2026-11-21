import type { ModuleViewType } from "@/features/college-admin/components/modules/generic-module-screen";

const DASHBOARD: Record<string, string> = {
  faculty: "/college-admin/faculty-administration/faculty",
  attendance: "/college-admin/attendance-administration/summaries/departments",
  examinations: "/college-admin/examination-administration/dashboard/page",
  finance: "/college-admin/finance-administration/reports/summary",
  hr: "/college-admin/hr-administration/statistics",
  library: "/college-admin/library-administration/reports/summary",
  hostel: "/college-admin/hostel-administration/reports/occupancy",
  communication: "/college-admin/communication-administration/reports/summary",
  lms: "/college-admin/lms-administration/statistics",
  reports: "/college-admin/reports-analytics/dashboard",
  approvals: "/college-admin/workflow-administration/pending",
  security: "/college-admin/security-administration/reports/summary",
  "data-import": "/college-admin/data-import/templates",
  integrations: "/college-admin/integration-administration/integrations",
  helpdesk: "/college-admin/helpdesk/reports/performance",
  "finance-extensions": "/college-admin/finance-extensions/budgets",
  operations: "/college-admin/operations-extensions/reports/summary",
  shared: "/college-admin/dashboard",
};

const SLUG_API: Record<string, string> = {
  // CA 07
  "faculty-directory": "/college-admin/faculty-administration/faculty",
  "employee-directory": "/college-admin/faculty-administration/faculty",
  "faculty-profile": "/college-admin/faculty-administration/faculty",
  "faculty-employee-history": "/college-admin/faculty-administration/faculty",
  // CA 08
  "attendance-rules-policies": "/college-admin/attendance-administration/policies",
  "attendance-correction-requests": "/college-admin/attendance-administration/corrections",
  "attendance-shortage-report": "/college-admin/attendance-administration/shortages",
  "department-wise-attendance": "/college-admin/attendance-administration/summaries/departments",
  "attendance-reports": "/college-admin/attendance-administration/reports/compliance",
  "student-attendance-overview": "/college-admin/attendance-administration/summaries/departments",
  "faculty-attendance-overview": "/college-admin/attendance-administration/summaries/departments",
  "subject-wise-attendance": "/college-admin/attendance-administration/history",
  "attendance-monitoring": "/college-admin/attendance-administration/submissions/missing",
  // CA 09
  "examination-dashboard": "/college-admin/examination-administration/dashboard/page",
  "examination-session-management": "/college-admin/examination-administration/sessions/page",
  "examination-configuration": "/college-admin/examination-administration/sessions/setup/page",
  "exam-timetable-management": "/college-admin/examination-administration/timetable/page",
  "exam-registration-management":
    "/college-admin/examination-administration/registrations/page",
  "student-exam-eligibility": "/college-admin/examination-administration/eligibility/students/page",
  "hall-ticket-administration": "/college-admin/examination-administration/hall-tickets/page",
  "examination-hall-seating-management": "/college-admin/examination-administration/halls-seating/page",
  "invigilator-allocation": "/college-admin/examination-administration/invigilation/page",
  "marks-entry-management": "/college-admin/examination-administration/marks-entry/page",
  "internal-external-assessment": "/college-admin/examination-administration/assessment-pattern/page",
  "result-processing": "/college-admin/examination-administration/results/processing/page",
  "result-approval": "/college-admin/examination-administration/results/approval/page",
  "result-publication": "/college-admin/examination-administration/results/publication/page",
  "revaluation-management": "/college-admin/examination-administration/revaluation/page",
  "supplementary-examination-management": "/college-admin/examination-administration/supplementary/page",
  "examination-reports": "/college-admin/examination-administration/reports",
  // CA 10
  "fee-structure-management": "/college-admin/finance-administration/fee-structures",
  "payment-transactions": "/college-admin/finance-administration/transactions",
  "financial-reports": "/college-admin/finance-administration/reports/summary",
  "fee-concession-waiver-management": "/college-admin/finance-administration/concessions",
  "refund-management": "/college-admin/finance-administration/refunds",
  // CA 11
  "hr-reports": "/college-admin/hr-administration/reports/summary",
  "leave-management": "/college-admin/hr-administration/leave/pending",
  "payroll-processing": "/college-admin/hr-administration/payroll/status",
  // CA 12
  "library-reports": "/college-admin/library-administration/reports/summary",
  "book-issue-return-management": "/college-admin/library-administration/circulation",
  // CA 13
  "hostel-reports": "/college-admin/hostel-administration/reports/occupancy",
  "hostel-admission-applications": "/college-admin/hostel-administration/waiting-list",
  // CA 14
  "delivery-status-monitoring": "/college-admin/communication-administration/deliveries/failed",
  "communication-history": "/college-admin/communication-administration/deliveries/failed",
  // CA 15
  "lms-reports": "/college-admin/lms-administration/monitoring",
  "subject-course-mapping": "/college-admin/lms-administration/course-mappings",
  "lms-settings": "/college-admin/lms-administration/settings",
  // CA 16
  "export-download-history": "/college-admin/reports-analytics/exports/download",
  "scheduled-reports": "/college-admin/reports-analytics/jobs",
  // CA 17
  "pending-approval-requests": "/college-admin/workflow-administration/pending",
  "escalation-management": "/college-admin/workflow-administration/escalations",
  // CA 18
  "administrative-audit-logs": "/college-admin/security-administration/audit-logs",
  "login-history": "/college-admin/security-administration/login-activity",
  "security-events": "/college-admin/security-administration/security-events",
  // CA 19 data import
  "import-history": "/college-admin/data-import/migration-history?limit=50&offset=0",
  "import-templates": "/college-admin/data-import/templates",
  "data-import-dashboard": "/college-admin/data-import/templates",
  // CA 20 integrations
  "available-integrations": "/college-admin/integration-administration/integrations",
  "integration-error-monitoring": "/college-admin/integration-administration/integrations",
  // CA 21 helpdesk
  "all-support-tickets": "/college-admin/helpdesk/tickets?limit=50&offset=0",
  "support-ticket-details": "/college-admin/helpdesk/tickets",
  // CA 03 users
  "all-users-list": "/college-admin/users?limit=50&offset=0",
  // CA 04 organization
  "all-departments": "/college-admin/departments?limit=200&offset=0",
  "organizational-hierarchy": "/college-admin/organization/hierarchy/page",
  "programme-course-mapping": "/college-admin/departments/programme-course-mapping/page",
  "department-faculty-allocation": "/college-admin/departments/faculty-allocation/page",
  "department-status-history": "/college-admin/departments/status-history/page",
  "department-resource-management": "/college-admin/departments/resource-management/page",
  // CA 05 academics
  "all-programmes": "/college-admin/academic-config/programmes",
  "course-catalogue": "/college-admin/academic-config/courses",
};

export function inferViewType(slug: string): ModuleViewType {
  const s = slug.toLowerCase();
  if (s.includes("dashboard")) return "dashboard";
  if (/(report|reconciliation|monitoring|overview)/.test(s)) return "report";
  if (
    /(add-new|create-|management|configuration|allocation|assignment|settings|entry|approval|publication|verification|collection|revaluation|scholarship|concession|refund|invoice|demand|registration|timetable|session|processing|onboarding|recruitment|acquisition|checkout|mess-|visitor-|templates|scheduled-)/.test(
      s,
    )
  )
    return "form";
  if (/(profile|history|details|eligibility)/.test(s)) return "detail";
  return "list";
}

export function resolveModuleEndpoint(
  moduleKey: string,
  slug: string,
): { apiPath: string; viewType: ModuleViewType } {
  const apiPath =
    SLUG_API[slug] ??
    (slug.includes("dashboard")
      ? DASHBOARD[moduleKey]
      : DASHBOARD[moduleKey] ?? "/college-admin/dashboard");
  return { apiPath, viewType: inferViewType(slug) };
}