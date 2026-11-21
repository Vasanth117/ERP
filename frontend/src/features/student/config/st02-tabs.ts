import type { CollegeAdminTab } from "@/features/college-admin/config/section-tabs";

/** Figma ST 02 — module tabs (node 164:3627). */
export const studentSt02Tabs: CollegeAdminTab[] = [
  {
    label: "Overview",
    href: "/student/academics",
    figmaFrame: "164:3628",
  },
  {
    label: "Semesters",
    href: "/student/academics/enrollment-history",
    figmaFrame: "164:3630",
  },
  {
    label: "Subjects & credits",
    href: "/student/academics/eligibility",
    figmaFrame: "164:3632",
  },
  {
    label: "Enrollment",
    href: "/student/academics/enrollment-requests",
    activePrefixes: [
      "/student/academics/enrollment-requests",
      "/student/academics/new-enrollment-request",
    ],
    figmaFrame: "164:3634",
  },
  {
    label: "Status",
    href: "/student/academics/enrollment-status",
    figmaFrame: "164:3636",
  },
];

const ST02_PATHS = [
  "/student/academics",
  "/student/academics/enrollment-history",
  "/student/academics/eligibility",
  "/student/academics/enrollment-requests",
  "/student/academics/new-enrollment-request",
  "/student/academics/enrollment-status",
];

export function isStudentSt02Path(pathname: string): boolean {
  return ST02_PATHS.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`),
  );
}
