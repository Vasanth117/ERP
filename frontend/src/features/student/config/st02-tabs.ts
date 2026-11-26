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
    figmaFrame: "164:4676",
  },
  {
    label: "Subjects & Credits",
    href: "/student/academics/eligibility",
    figmaFrame: "164:5744",
  },
  {
    label: "Enrollment",
    href: "/student/academics/enrollment-details",
    activePrefixes: [
      "/student/academics/enrollment-details",
      "/student/academics/enrollment-requests",
      "/student/academics/new-enrollment-request",
    ],
    figmaFrame: "164:6396",
  },
  {
    label: "Status",
    href: "/student/academics/enrollment-status",
    figmaFrame: "164:6990",
  },
  {
    label: "Programme & Department",
    href: "/student/academics/programme-department",
    figmaFrame: "164:4368",
  },
];

const ST02_PATHS = [
  "/student/academics",
  "/student/academics/enrollment-history",
  "/student/academics/eligibility",
  "/student/academics/enrollment-details",
  "/student/academics/enrollment-requests",
  "/student/academics/new-enrollment-request",
  "/student/academics/enrollment-status",
  "/student/academics/programme-department",
];

export function isStudentSt02Path(pathname: string): boolean {
  return ST02_PATHS.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`),
  );
}
