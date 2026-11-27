import type { CollegeAdminTab } from "@/features/college-admin/config/section-tabs";

/** Figma ST 05 — module tabs (overview 164:14234). */
export const studentSt05Tabs: CollegeAdminTab[] = [
  {
    label: "Overview",
    href: "/student/timetable",
    figmaFrame: "164:14234",
  },
  {
    label: "Timetable",
    href: "/student/timetable/schedule",
    figmaFrame: "164:14590",
  },
  {
    label: "Calendar",
    href: "/student/timetable/calendar",
    figmaFrame: "ST 05",
  },
  {
    label: "Examinations",
    href: "/student/timetable/examinations",
    figmaFrame: "ST 05",
  },
  {
    label: "Changes",
    href: "/student/timetable/changes",
    activePrefixes: [
      "/student/timetable/changes",
      "/student/timetable/notifications",
      "/student/timetable/cancelled-sessions",
    ],
    figmaFrame: "ST 05",
  },
];

const ST05_PATHS = [
  "/student/timetable",
  "/student/timetable/schedule",
  "/student/timetable/daily",
  "/student/timetable/weekly",
  "/student/timetable/month",
  "/student/timetable/laboratory",
  "/student/timetable/semester",
  "/student/timetable/calendar",
  "/student/timetable/deadlines",
  "/student/timetable/examinations",
  "/student/timetable/changes",
  "/student/timetable/notifications",
  "/student/timetable/cancelled-sessions",
];

export function isStudentSt05Path(pathname: string): boolean {
  return ST05_PATHS.some((p) => pathname === p || pathname.startsWith(`${p}/`));
}

/** ST 05 — Overview highlights only on exact `/student/timetable`. */
export function isStudentSt05TabActive(pathname: string, tab: CollegeAdminTab): boolean {
  if (tab.href === "/student/timetable") {
    return pathname === tab.href;
  }
  if (tab.activePrefixes?.length) {
    return tab.activePrefixes.some(
      (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
    );
  }
  return pathname === tab.href || pathname.startsWith(`${tab.href}/`);
}