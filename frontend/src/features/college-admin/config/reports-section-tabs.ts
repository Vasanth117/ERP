/** Figma CA 16 — reports & analytics (grouped section nav). */
export const reportsSectionTabs = [
  {
    label: "Overview",
    href: "/college-admin/reports/reports-dashboard",
    figmaFrame: "161:14939",
    activePrefixes: ["/college-admin/reports/reports-dashboard", "/college-admin/reports/analytics-dashboard"],
  },
  {
    label: "Academic",
    href: "/college-admin/reports/student-reports",
    figmaFrame: "161:15072",
    activePrefixes: [
      "/college-admin/reports/student-reports",
      "/college-admin/reports/department-reports",
      "/college-admin/reports/academic-performance-reports",
      "/college-admin/reports/attendance-reports",
      "/college-admin/reports/examination-reports",
    ],
  },
  {
    label: "People",
    href: "/college-admin/reports/faculty-employee-reports",
    figmaFrame: "161:15194",
    activePrefixes: [
      "/college-admin/reports/faculty-employee-reports",
      "/college-admin/reports/hr-reports",
    ],
  },
  {
    label: "Operations",
    href: "/college-admin/reports/finance-reports",
    figmaFrame: "161:15316",
    activePrefixes: [
      "/college-admin/reports/finance-reports",
      "/college-admin/reports/library-reports",
      "/college-admin/reports/hostel-reports",
    ],
  },
  {
    label: "Custom & scheduled",
    href: "/college-admin/reports/custom-report-builder",
    figmaFrame: "161:15438",
    activePrefixes: [
      "/college-admin/reports/custom-report-builder",
      "/college-admin/reports/scheduled-reports",
      "/college-admin/reports/export-download-history",
    ],
  },
] satisfies ReadonlyArray<{
  label: string;
  href: string;
  figmaFrame: string;
  activePrefixes?: string[];
}>;