/** Figma CA 06 — student administration (section nav; detail routes use activePrefixes). */
export const studentsSectionTabs = [
  {
    label: "Overview",
    href: "/college-admin/students/student-administration-dashboard",
    figmaFrame: "69:145600",
  },
  {
    label: "All students",
    href: "/college-admin/students/all-students-list",
    figmaFrame: "69:145896",
    activePrefixes: [
      "/college-admin/students/all-students-list",
      "/college-admin/students/student-details",
      "/college-admin/students/create-student",
    ],
  },
  {
    label: "Admissions",
    href: "/college-admin/students/student-admission",
    figmaFrame: "158:2987",
    activePrefixes: [
      "/college-admin/students/student-admission",
      "/college-admin/students/new-student-registration",
      "/college-admin/students/admissions-list",
      "/college-admin/students/bulk-student-import",
    ],
  },
  {
    label: "Profiles & documents",
    href: "/college-admin/students/student-profile-management",
    figmaFrame: "158:3788",
    activePrefixes: [
      "/college-admin/students/student-profile-management",
      "/college-admin/students/student-document-verification",
      "/college-admin/students/profile-corrections",
    ],
  },
  {
    label: "Enrollment",
    href: "/college-admin/students/student-enrollment-management",
    figmaFrame: "158:4489",
  },
  {
    label: "Sections",
    href: "/college-admin/students/batch-section-allocation",
    figmaFrame: "158:4860",
    activePrefixes: [
      "/college-admin/students/batch-section-allocation",
      "/college-admin/students/section-transfer-review",
    ],
  },
  {
    label: "Transfers & promotions",
    href: "/college-admin/students/student-transfer-management",
    figmaFrame: "158:5236",
    activePrefixes: [
      "/college-admin/students/student-transfer-management",
      "/college-admin/students/student-promotion-management",
    ],
  },
  {
    label: "Status",
    href: "/college-admin/students/student-status-management",
    figmaFrame: "158:5911",
    activePrefixes: [
      "/college-admin/students/student-status-management",
      "/college-admin/students/student-withdrawal-discontinuation",
    ],
  },
  {
    label: "ID cards",
    href: "/college-admin/students/student-id-card-management",
    figmaFrame: "158:6282",
  },
  {
    label: "History",
    href: "/college-admin/students/student-academic-history",
    figmaFrame: "158:7002",
    activePrefixes: [
      "/college-admin/students/student-academic-history",
      "/college-admin/students/academic-history",
    ],
  },
] satisfies ReadonlyArray<{
  label: string;
  href: string;
  figmaFrame: string;
  activePrefixes?: string[];
}>;