/** Figma CA 11 — human resources (grouped section nav). */
export const hrSectionTabs = [
  {
    label: "Overview",
    href: "/college-admin/hr/hr-dashboard",
    figmaFrame: "160:7148",
    activePrefixes: [
      "/college-admin/hr/hr-dashboard",
      "/college-admin/hr/hr-statistics",
    ],
  },
  {
    label: "Employees",
    href: "/college-admin/hr/employee-management",
    figmaFrame: "160:7538",
    activePrefixes: [
      "/college-admin/hr/employee-management",
      "/college-admin/hr/employee-detail",
    ],
  },
  {
    label: "Recruitment & onboarding",
    href: "/college-admin/hr/recruitment-management",
    figmaFrame: "160:7882",
    activePrefixes: [
      "/college-admin/hr/recruitment-management",
      "/college-admin/hr/employee-onboarding",
    ],
  },
  {
    label: "Attendance & leave",
    href: "/college-admin/hr/employee-attendance",
    figmaFrame: "160:8512",
    activePrefixes: [
      "/college-admin/hr/employee-attendance",
      "/college-admin/hr/leave-management",
      "/college-admin/hr/leave-approval",
      "/college-admin/hr/pending-leave",
    ],
  },
  {
    label: "Payroll",
    href: "/college-admin/hr/payroll-processing",
    figmaFrame: "160:9787",
    activePrefixes: [
      "/college-admin/hr/salary-structure-management",
      "/college-admin/hr/payroll-processing",
      "/college-admin/hr/salary-slip-management",
      "/college-admin/hr/payroll-status",
    ],
  },
  {
    label: "Benefits & performance",
    href: "/college-admin/hr/employee-benefits-claims",
    figmaFrame: "160:10410",
    activePrefixes: [
      "/college-admin/hr/employee-benefits-claims",
      "/college-admin/hr/performance-management",
    ],
  },
  {
    label: "Reports & settings",
    href: "/college-admin/hr/hr-reports",
    figmaFrame: "160:10983",
    activePrefixes: [
      "/college-admin/hr/hr-reports",
      "/college-admin/hr/hr-summary-report",
      "/college-admin/hr/hr-settings-policies",
    ],
  },
] satisfies ReadonlyArray<{
  label: string;
  href: string;
  figmaFrame: string;
  activePrefixes?: string[];
}>;