import type { CollegeAdminTab } from "@/features/college-admin/config/section-tabs";

/** Figma ST 03 — module tabs (node 164:7289). */
export const studentSt03Tabs: CollegeAdminTab[] = [
  {
    label: "Overview",
    href: "/student/curriculum",
    figmaFrame: "164:7290",
  },
  {
    label: "Semester curriculum",
    href: "/student/curriculum/programme",
    figmaFrame: "164:7641",
  },
  {
    label: "Subjects",
    href: "/student/curriculum/semester-subjects",
    figmaFrame: "164:7994",
  },
  {
    label: "Syllabus",
    href: "/student/curriculum/course-syllabus",
    activePrefixes: [
      "/student/curriculum/course-syllabus",
      "/student/curriculum/learning-outcomes",
      "/student/curriculum/course-prerequisites",
      "/student/curriculum/course-information",
    ],
    figmaFrame: "164:8701",
  },
  {
    label: "Categories & electives",
    href: "/student/curriculum/enrolled-courses",
    figmaFrame: "165:64048",
  },
  {
    label: "History",
    href: "/student/curriculum/history",
    figmaFrame: "164:10272",
  },
];

const ST03_PATHS = [
  "/student/curriculum",
  "/student/curriculum/programme",
  "/student/curriculum/enrolled-courses",
  "/student/curriculum/semester-subjects",
  "/student/curriculum/course-syllabus",
  "/student/curriculum/learning-outcomes",
  "/student/curriculum/course-prerequisites",
  "/student/curriculum/course-information",
  "/student/curriculum/history",
];

export function isStudentSt03Path(pathname: string): boolean {
  return ST03_PATHS.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`),
  );
}