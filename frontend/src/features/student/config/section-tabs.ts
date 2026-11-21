import type { CollegeAdminTab } from "@/features/college-admin/config/section-tabs";

import { studentNavGroups } from "@/features/student/config/navigation";

export type StudentModuleKey =
  | "overview"
  | "academics"
  | "curriculum"
  | "registration"
  | "timetable"
  | "attendance"
  | "cia"
  | "assessments";

export type StudentModuleChromeDef = {
  key: StudentModuleKey;
  title: string;
  description: string;
  figmaPage: string;
  navGroupTitle: string;
};

/** Figma ST modules — module title + horizontal tabs (mirrors college-admin section chrome). */
export const studentModuleChrome: Record<StudentModuleKey, StudentModuleChromeDef> = {
  overview: {
    key: "overview",
    title: "Student Portal",
    description: "Dashboard, profile, and daily academic workspace — same layout pattern as College Admin.",
    figmaPage: "ST 01",
    navGroupTitle: "OVERVIEW",
  },
  academics: {
    key: "academics",
    title: "Academic Management & Enrollment",
    description: "Enrollment standing, history, eligibility, and change requests.",
    figmaPage: "ST 02",
    navGroupTitle: "ACADEMICS",
  },
  curriculum: {
    key: "curriculum",
    title: "Course, Subject & Curriculum",
    description: "Programme structure, enrolled courses, and course details.",
    figmaPage: "ST 03",
    navGroupTitle: "CURRICULUM",
  },
  registration: {
    key: "registration",
    title: "Course Registration & Electives",
    description: "Registration windows, course selection, and submission history.",
    figmaPage: "ST 04",
    navGroupTitle: "REGISTRATION",
  },
  timetable: {
    key: "timetable",
    title: "Timetable & Academic Calendar",
    description: "Daily and weekly schedules, calendar events, and exam dates.",
    figmaPage: "ST 05",
    navGroupTitle: "TIMETABLE",
  },
  attendance: {
    key: "attendance",
    title: "Attendance & Shortage Tracking",
    description: "Attendance summaries, shortages, discrepancies, and exports.",
    figmaPage: "ST 06",
    navGroupTitle: "ATTENDANCE",
  },
  cia: {
    key: "cia",
    title: "Internal Assessment & CIA Marks",
    description: "CIA schedules, published marks, corrections, and components.",
    figmaPage: "ST 07",
    navGroupTitle: "CIA MARKS",
  },
  assessments: {
    key: "assessments",
    title: "Assignments, Quizzes & Continuous Assessment",
    description: "Assignments, quizzes, submissions, feedback, and resubmission.",
    figmaPage: "ST 08",
    navGroupTitle: "ASSESSMENTS",
  },
};

const MODULE_PREFIX: { key: StudentModuleKey; prefix: string }[] = [
  { key: "overview", prefix: "/student/dashboard" },
  { key: "overview", prefix: "/student/profile" },
  { key: "overview", prefix: "/student/documents" },
  { key: "academics", prefix: "/student/academics" },
  { key: "curriculum", prefix: "/student/curriculum" },
  { key: "registration", prefix: "/student/registration" },
  { key: "timetable", prefix: "/student/timetable" },
  { key: "attendance", prefix: "/student/attendance" },
  { key: "cia", prefix: "/student/cia" },
  { key: "assessments", prefix: "/student/assessments" },
];

export function resolveStudentModuleKey(pathname: string): StudentModuleKey | null {
  if (pathname === "/student" || pathname === "/student/home") {
    return "overview";
  }
  const hit = MODULE_PREFIX.find(
    (row) => pathname === row.prefix || pathname.startsWith(`${row.prefix}/`),
  );
  return hit?.key ?? null;
}

export function studentTabsForModule(key: StudentModuleKey): CollegeAdminTab[] {
  const def = studentModuleChrome[key];
  const group = studentNavGroups.find((g) => g.title === def.navGroupTitle);
  if (!group) return [];
  const tabs = group.items
    .filter((item) => item.id !== "portal-home")
    .map((item) => ({
      label: item.label,
      href: item.href,
      figmaFrame: item.figmaPage ?? def.figmaPage,
    }));
  if (key === "overview") {
    return [
      { label: "Workspace map", href: "/student/home", figmaFrame: "ST 00" },
      ...tabs,
    ];
  }
  return tabs;
}

const PORTAL_MODULE_LABEL: Record<StudentModuleKey, string> = {
  overview: "Overview & profile",
  academics: "Academics",
  curriculum: "Curriculum",
  registration: "Registration",
  timetable: "Timetable",
  attendance: "Attendance",
  cia: "CIA marks",
  assessments: "Assessments",
};

const OVERVIEW_PREFIXES = [
  "/student/dashboard",
  "/student/profile",
  "/student/documents",
  "/student/home",
];

export const studentPortalModuleTabs: CollegeAdminTab[] = (
  Object.keys(studentModuleChrome) as StudentModuleKey[]
).map((key) => {
  const def = studentModuleChrome[key];
  const group = studentNavGroups.find((g) => g.title === def.navGroupTitle);
  const first =
    group?.items.find((i) => i.id !== "portal-home") ?? group?.items[0];
  const activePrefixes =
    key === "overview"
      ? OVERVIEW_PREFIXES
      : MODULE_PREFIX.filter((r) => r.key === key).map((r) => r.prefix);
  return {
    label: PORTAL_MODULE_LABEL[key],
    href: first?.href ?? "/student/dashboard",
    figmaFrame: def.figmaPage,
    activePrefixes,
  };
});

export function isStudentTabActive(pathname: string, tab: CollegeAdminTab): boolean {
  if (tab.href === "/student/home") {
    return pathname === tab.href;
  }
  if (tab.href === "/student/dashboard") {
    return pathname === tab.href;
  }
  if (tab.href === "/student/profile") {
    if (pathname.startsWith("/student/profile/update-requests")) return false;
    return pathname === "/student/profile" || pathname.startsWith("/student/profile/");
  }
  if (tab.href === "/student/profile/update-requests") {
    return pathname === tab.href || pathname.startsWith(`${tab.href}/`);
  }
  if (tab.href === "/student/documents") {
    return pathname === tab.href || pathname.startsWith(`${tab.href}/`);
  }
  return pathname === tab.href || pathname.startsWith(`${tab.href}/`);
}