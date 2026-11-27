import type { ErpIconName } from "@/components/icons/erp/names";

/** Figma ST 00 — `ST / Sidebar` (node 163:3). Hub links only (not every workspace page). */
export type StudentSidebarNavItem = {
  id: string;
  label: string;
  href: string;
  icon: ErpIconName;
  figmaNode?: string;
};

export type StudentSidebarNavGroup = {
  title: string;
  items: StudentSidebarNavItem[];
};

export const studentSidebarNav: StudentSidebarNavGroup[] = [
  {
    title: "OVERVIEW",
    items: [
      {
        id: "dashboard",
        label: "Dashboard",
        href: "/student/dashboard",
        icon: "layout-dashboard",
        figmaNode: "163:207",
      },
      {
        id: "profile",
        label: "My Profile",
        href: "/student/profile",
        icon: "user-round",
        figmaNode: "163:217",
      },
    ],
  },
  {
    title: "ACADEMICS",
    items: [
      {
        id: "academic-overview",
        label: "Academic Overview",
        href: "/student/academics",
        icon: "book-open",
        figmaNode: "163:235",
      },
      {
        id: "curriculum",
        label: "Courses & Curriculum",
        href: "/student/curriculum",
        icon: "layers",
        figmaNode: "163:243",
      },
      {
        id: "registration",
        label: "Course Registration",
        href: "/student/registration",
        icon: "square-check",
        figmaNode: "163:252",
      },
      {
        id: "timetable",
        label: "Timetable & Calendar",
        href: "/student/timetable",
        icon: "calendar-days",
        figmaNode: "163:259",
      },
      {
        id: "attendance",
        label: "Attendance",
        href: "/student/attendance",
        icon: "clipboard-check",
        figmaNode: "163:267",
      },
      {
        id: "cia",
        label: "Internal Assessment",
        href: "/student/cia",
        icon: "file-text",
        figmaNode: "163:276",
      },
      {
        id: "assessments",
        label: "Assignments & Quizzes",
        href: "/student/assessments",
        icon: "pencil",
        figmaNode: "163:284",
      },
      {
        id: "laboratory",
        label: "Laboratory & Practicals",
        href: "/under-construction?module=student-laboratory",
        icon: "flask-conical",
        figmaNode: "163:292",
      },
    ],
  },
  {
    title: "EXAMINATIONS & RESULTS",
    items: [
      {
        id: "examinations",
        label: "Examinations",
        href: "/under-construction?module=student-examinations",
        icon: "id-card",
        figmaNode: "163:309",
      },
      {
        id: "exam-registration",
        label: "Registration & Hall Ticket",
        href: "/under-construction?module=student-exam-registration",
        icon: "ticket",
        figmaNode: "163:318",
      },
      {
        id: "results",
        label: "Results & Marks",
        href: "/under-construction?module=student-results",
        icon: "chart-bar",
        figmaNode: "163:327",
      },
      {
        id: "gpa",
        label: "GPA & CGPA",
        href: "/under-construction?module=student-gpa",
        icon: "arrow-up",
        figmaNode: "163:335",
      },
      {
        id: "marksheets",
        label: "Marksheets & Transcripts",
        href: "/under-construction?module=student-marksheets",
        icon: "file-text",
        figmaNode: "163:342",
      },
      {
        id: "arrears",
        label: "Arrears & Supplementary",
        href: "/under-construction?module=student-arrears",
        icon: "refresh-cw",
        figmaNode: "163:350",
      },
      {
        id: "revaluation",
        label: "Revaluation Requests",
        href: "/under-construction?module=student-revaluation",
        icon: "shuffle",
        figmaNode: "163:360",
      },
    ],
  },
  {
    title: "LEARNING & FINANCE",
    items: [
      {
        id: "lms",
        label: "LMS & Materials",
        href: "/under-construction?module=student-lms",
        icon: "monitor-play",
        figmaNode: "163:377",
      },
      {
        id: "fees",
        label: "Fees & Payments",
        href: "/under-construction?module=student-fees",
        icon: "wallet",
        figmaNode: "163:386",
      },
      {
        id: "scholarships",
        label: "Scholarships",
        href: "/under-construction?module=student-scholarships",
        icon: "graduation-cap",
        figmaNode: "163:394",
      },
    ],
  },
  {
    title: "CAMPUS & SERVICES",
    items: [
      {
        id: "library",
        label: "Library",
        href: "/under-construction?module=student-library",
        icon: "library-big",
        figmaNode: "163:412",
      },
      {
        id: "hostel",
        label: "Hostel",
        href: "/under-construction?module=student-hostel",
        icon: "hotel",
        figmaNode: "163:419",
      },
      {
        id: "transport",
        label: "Transport",
        href: "/under-construction?module=student-transport",
        icon: "map-pin",
        figmaNode: "163:426",
      },
    ],
  },
  {
    title: "COMMUNICATION & SUPPORT",
    items: [
      {
        id: "notifications",
        label: "Notifications",
        href: "/student/dashboard",
        icon: "info",
        figmaNode: "163:444",
      },
      {
        id: "announcements",
        label: "Announcements",
        href: "/under-construction?module=student-announcements",
        icon: "megaphone",
        figmaNode: "163:452",
      },
      {
        id: "documents",
        label: "Documents",
        href: "/student/documents",
        icon: "copy",
        figmaNode: "163:460",
      },
      {
        id: "requests",
        label: "My Requests",
        href: "/under-construction?module=student-requests",
        icon: "send",
        figmaNode: "163:468",
      },
      {
        id: "support",
        label: "Support",
        href: "/under-construction?module=student-support",
        icon: "life-buoy",
        figmaNode: "163:476",
      },
      {
        id: "reports",
        label: "Reports",
        href: "/under-construction?module=student-reports",
        icon: "chart-bar",
        figmaNode: "163:484",
      },
      {
        id: "account-settings",
        label: "Account Settings",
        href: "/student/profile",
        icon: "settings-2",
        figmaNode: "163:492",
      },
    ],
  },
];

export const studentSidebarFlat = studentSidebarNav.flatMap((g) => g.items);

export function sidebarNavActive(pathname: string, href: string): boolean {
  if (href.startsWith("/under-construction")) {
    return false;
  }
  if (href === "/student/dashboard") {
    return pathname === href;
  }
  if (href === "/student/profile") {
    return pathname === href || pathname.startsWith("/student/profile/");
  }
  if (href === "/student/academics") {
    return pathname === href || pathname.startsWith(`${href}/`);
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}