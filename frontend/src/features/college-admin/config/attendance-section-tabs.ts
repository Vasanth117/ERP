/** Figma CA 08 — attendance administration (section nav; detail routes use activePrefixes). */
export const attendanceSectionTabs = [
  {
    label: "Overview",
    href: "/college-admin/attendance/attendance-dashboard",
    figmaFrame: "159:6844",
    activePrefixes: [
      "/college-admin/attendance/attendance-dashboard",
      "/college-admin/attendance/department-wise-attendance",
      "/college-admin/attendance/subject-wise-attendance",
      "/college-admin/attendance/department-summaries",
      "/college-admin/attendance/session-history",
    ],
  },
  {
    label: "Student attendance",
    href: "/college-admin/attendance/student-attendance-overview",
    figmaFrame: "159:7247",
  },
  {
    label: "Faculty attendance",
    href: "/college-admin/attendance/faculty-attendance-overview",
    figmaFrame: "159:7592",
  },
  {
    label: "Monitoring",
    href: "/college-admin/attendance/attendance-monitoring",
    figmaFrame: "159:8573",
    activePrefixes: [
      "/college-admin/attendance/attendance-monitoring",
      "/college-admin/attendance/attendance-shortage-report",
      "/college-admin/attendance/attendance-shortages",
      "/college-admin/attendance/missing-submissions",
    ],
  },
  {
    label: "Corrections",
    href: "/college-admin/attendance/attendance-correction-requests",
    figmaFrame: "159:9222",
    activePrefixes: [
      "/college-admin/attendance/attendance-correction-requests",
      "/college-admin/attendance/correction-requests",
      "/college-admin/attendance/attendance-approval",
    ],
  },
  {
    label: "Configuration",
    href: "/college-admin/attendance/attendance-configuration",
    figmaFrame: "159:9831",
    activePrefixes: [
      "/college-admin/attendance/attendance-configuration",
      "/college-admin/attendance/attendance-rules-policies",
      "/college-admin/attendance/attendance-policies",
    ],
  },
  {
    label: "Reports",
    href: "/college-admin/attendance/attendance-reports",
    figmaFrame: "159:10420",
    activePrefixes: [
      "/college-admin/attendance/attendance-reports",
      "/college-admin/attendance/compliance-reports",
    ],
  },
] satisfies ReadonlyArray<{
  label: string;
  href: string;
  figmaFrame: string;
  activePrefixes?: string[];
}>;