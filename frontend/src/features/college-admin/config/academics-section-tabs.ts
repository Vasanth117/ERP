/** Figma CA 05 — academic configuration (section nav; detail routes use activePrefixes). */
export const academicsTabs = [
  {
    label: "Overview",
    href: "/college-admin/academics/academic-configuration-dashboard",
    figmaFrame: "69:139646",
  },
  {
    label: "Years & semesters",
    href: "/college-admin/academics/academic-year-management",
    figmaFrame: "69:139876",
    activePrefixes: [
      "/college-admin/academics/academic-year-management",
      "/college-admin/academics/semester-management",
    ],
  },
  {
    label: "Programmes",
    href: "/college-admin/academics/programme-management",
    figmaFrame: "69:140372",
  },
  {
    label: "Courses & curriculum",
    href: "/college-admin/academics/course-configuration",
    figmaFrame: "69:140676",
    activePrefixes: [
      "/college-admin/academics/course-configuration",
      "/college-admin/academics/curriculum-management",
      "/college-admin/academics/subject-management",
    ],
  },
  {
    label: "Credits & grading",
    href: "/college-admin/academics/credit-configuration",
    figmaFrame: "69:141424",
    activePrefixes: [
      "/college-admin/academics/credit-configuration",
      "/college-admin/academics/grading-system-configuration",
    ],
  },
  {
    label: "Regulations",
    href: "/college-admin/academics/regulation-management",
    figmaFrame: "69:141649",
  },
  {
    label: "Calendar",
    href: "/college-admin/academics/academic-calendar-configuration",
    figmaFrame: "69:142093",
  },
  {
    label: "Batches",
    href: "/college-admin/academics/batch-section-configuration",
    figmaFrame: "69:142356",
  },
  {
    label: "History",
    href: "/college-admin/academics/academic-configuration-history",
    figmaFrame: "69:142605",
  },
] satisfies ReadonlyArray<{
  label: string;
  href: string;
  figmaFrame: string;
  activePrefixes?: string[];
}>;