/** Figma CA 07 — faculty & employees (section nav; detail routes use activePrefixes). */
export const facultySectionTabs = [
  {
    label: "Overview",
    href: "/college-admin/faculty/faculty-employee-dashboard",
    figmaFrame: "159:2199",
  },
  {
    label: "Faculty",
    href: "/college-admin/faculty/faculty-directory",
    figmaFrame: "159:2648",
    activePrefixes: [
      "/college-admin/faculty/faculty-directory",
      "/college-admin/faculty/faculty-profile",
      "/college-admin/faculty/all-faculty-list",
      "/college-admin/faculty/faculty-details",
      "/college-admin/faculty/create-faculty",
      "/college-admin/faculty/bulk-faculty-import",
      "/college-admin/faculty/faculty-transfer",
      "/college-admin/faculty/faculty-history",
      "/college-admin/faculty/add-new-faculty-employee",
    ],
  },
  {
    label: "Employees",
    href: "/college-admin/faculty/employee-directory",
    figmaFrame: "159:3382",
    activePrefixes: [
      "/college-admin/faculty/employee-directory",
      "/college-admin/faculty/employee-profile-management",
    ],
  },
  {
    label: "Assignments",
    href: "/college-admin/faculty/department-designation-assignment",
    figmaFrame: "159:4430",
    activePrefixes: [
      "/college-admin/faculty/department-designation-assignment",
      "/college-admin/faculty/faculty-subject-allocation",
      "/college-admin/faculty/teaching-assignments",
    ],
  },
  {
    label: "Workload & timetable",
    href: "/college-admin/faculty/faculty-workload-management",
    figmaFrame: "159:5133",
    activePrefixes: [
      "/college-admin/faculty/faculty-workload-management",
      "/college-admin/faculty/faculty-timetable",
      "/college-admin/faculty/workload-management",
    ],
  },
  {
    label: "Documents",
    href: "/college-admin/faculty/employee-document-verification",
    figmaFrame: "159:5832",
    activePrefixes: [
      "/college-admin/faculty/employee-document-verification",
      "/college-admin/faculty/faculty-documents",
    ],
  },
  {
    label: "Status & history",
    href: "/college-admin/faculty/employee-status-management",
    figmaFrame: "159:6175",
    activePrefixes: [
      "/college-admin/faculty/employee-status-management",
      "/college-admin/faculty/faculty-employee-history",
    ],
  },
] satisfies ReadonlyArray<{
  label: string;
  href: string;
  figmaFrame: string;
  activePrefixes?: string[];
}>;