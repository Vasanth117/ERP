import type { CollegeAdminTab } from "@/features/college-admin/config/section-tabs";

/** Figma ST 04 — module tabs (overview 164:10577 / closed 164:13961). */
export const studentSt04Tabs: CollegeAdminTab[] = [
  {
    label: "Overview",
    href: "/student/registration",
    figmaFrame: "164:10577",
  },
  {
    label: "Course",
    href: "/student/registration/courses",
    activePrefixes: [
      "/student/registration/courses",
      "/student/registration/available-courses",
    ],
    figmaFrame: "164:10975",
  },
  {
    label: "Elective",
    href: "/student/registration/electives",
    activePrefixes: [
      "/student/registration/electives",
      "/student/registration/elective-groups",
    ],
    figmaFrame: "164:11935",
  },
  {
    label: "Review & submit",
    href: "/student/registration/submit",
    activePrefixes: [
      "/student/registration/submit",
      "/student/registration/eligibility",
    ],
    figmaFrame: "ST 04",
  },
  {
    label: "Status & history",
    href: "/student/registration/history",
    activePrefixes: [
      "/student/registration/history",
      "/student/registration/my-registrations",
    ],
    figmaFrame: "164:13326",
  },
];

const ST04_PATHS = [
  "/student/registration",
  "/student/registration/courses",
  "/student/registration/available-courses",
  "/student/registration/electives",
  "/student/registration/elective-groups",
  "/student/registration/submit",
  "/student/registration/eligibility",
  "/student/registration/history",
  "/student/registration/my-registrations",
];

export function isStudentSt04Path(pathname: string): boolean {
  return ST04_PATHS.some((p) => pathname === p || pathname.startsWith(`${p}/`));
}

/** ST 04 module tabs — Overview is exact-match only (no highlight on sub-routes). */
export function isStudentSt04TabActive(pathname: string, tab: CollegeAdminTab): boolean {
  if (tab.href === "/student/registration") {
    return pathname === tab.href;
  }
  if (tab.activePrefixes?.length) {
    return tab.activePrefixes.some(
      (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
    );
  }
  return pathname === tab.href || pathname.startsWith(`${tab.href}/`);
}