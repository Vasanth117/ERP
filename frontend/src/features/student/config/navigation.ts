import type { ErpIconName } from "@/components/icons/erp/names";

export type StudentNavItem = {
  id: string;
  label: string;
  href: string;
  icon: ErpIconName;
  figmaPage?: string;
};

export type StudentNavGroup = {
  title: string;
  icon: ErpIconName;
  items: StudentNavItem[];
};

/** ST 00–08 — routes mapped to Figma student portal pages. */
export const studentNavGroups: StudentNavGroup[] = [
  {
    title: "OVERVIEW",
    icon: "panels-top-left",
    items: [
      {
        id: "portal-home",
        label: "All Portal Pages",
        href: "/student/home",
        icon: "layout-grid",
        figmaPage: "ST 00",
      },
      {
        id: "dashboard",
        label: "Dashboard",
        href: "/student/dashboard",
        icon: "layout-dashboard",
        figmaPage: "ST 01",
      },
      {
        id: "profile",
        label: "My Profile",
        href: "/student/profile",
        icon: "user-round",
        figmaPage: "ST 01",
      },
      {
        id: "profile-activity",
        label: "Profile Activity",
        href: "/student/profile/activity",
        icon: "history",
        figmaPage: "ST 01",
      },
    ],
  },
  {
    title: "ACADEMICS",
    icon: "graduation-cap",
    items: [
      {
        id: "academics-overview",
        label: "Academic Overview",
        href: "/student/academics",
        icon: "book-open",
        figmaPage: "ST 02",
      },
      {
        id: "enrollment-status",
        label: "Enrollment Status",
        href: "/student/academics/enrollment-status",
        icon: "badge-check",
        figmaPage: "ST 02",
      },
      {
        id: "enrollment-history",
        label: "Enrollment History",
        href: "/student/academics/enrollment-history",
        icon: "archive",
        figmaPage: "ST 02",
      },
      {
        id: "academic-eligibility",
        label: "Academic Eligibility",
        href: "/student/academics/eligibility",
        icon: "scale",
        figmaPage: "ST 02",
      },
      {
        id: "enrollment-requests",
        label: "Enrollment Requests",
        href: "/student/academics/enrollment-requests",
        icon: "file-stack",
        figmaPage: "ST 02",
      },
      {
        id: "new-enrollment-request",
        label: "New Request",
        href: "/student/academics/new-enrollment-request",
        icon: "file-plus",
        figmaPage: "ST 02",
      },
    ],
  },
  {
    title: "CURRICULUM",
    icon: "library-big",
    items: [
      {
        id: "curriculum-overview",
        label: "Curriculum Overview",
        href: "/student/curriculum",
        icon: "book-marked",
        figmaPage: "ST 03",
      },
      {
        id: "programme-curriculum",
        label: "Programme Curriculum",
        href: "/student/curriculum/programme",
        icon: "scroll-text",
        figmaPage: "ST 03",
      },
      {
        id: "enrolled-courses",
        label: "Enrolled Courses",
        href: "/student/curriculum/enrolled-courses",
        icon: "book-open-check",
        figmaPage: "ST 03",
      },
      {
        id: "semester-subjects",
        label: "Semester Subjects",
        href: "/student/curriculum/semester-subjects",
        icon: "list-ordered",
        figmaPage: "ST 03",
      },
      {
        id: "course-syllabus",
        label: "Course Syllabus",
        href: "/student/curriculum/course-syllabus",
        icon: "file-text",
        figmaPage: "ST 03",
      },
      {
        id: "learning-outcomes",
        label: "Learning Outcomes",
        href: "/student/curriculum/learning-outcomes",
        icon: "target",
        figmaPage: "ST 03",
      },
      {
        id: "course-prerequisites",
        label: "Prerequisites",
        href: "/student/curriculum/course-prerequisites",
        icon: "git-branch",
        figmaPage: "ST 03",
      },
      {
        id: "course-information",
        label: "Course Information",
        href: "/student/curriculum/course-information",
        icon: "info",
        figmaPage: "ST 03",
      },
    ],
  },
  {
    title: "REGISTRATION",
    icon: "clipboard-list",
    items: [
      {
        id: "registration-overview",
        label: "Registration Hub",
        href: "/student/registration",
        icon: "layout-list",
        figmaPage: "ST 04",
      },
      {
        id: "registration-eligibility",
        label: "Eligibility & Window",
        href: "/student/registration/eligibility",
        icon: "calendar-clock",
        figmaPage: "ST 04",
      },
      {
        id: "available-courses",
        label: "Available Courses",
        href: "/student/registration/available-courses",
        icon: "search",
        figmaPage: "ST 04",
      },
      {
        id: "elective-groups",
        label: "Elective Groups",
        href: "/student/registration/elective-groups",
        icon: "layers",
        figmaPage: "ST 04",
      },
      {
        id: "my-registrations",
        label: "My Registrations",
        href: "/student/registration/my-registrations",
        icon: "circle-check",
        figmaPage: "ST 04",
      },
      {
        id: "submit-registration",
        label: "Submit Registration",
        href: "/student/registration/submit",
        icon: "send",
        figmaPage: "ST 04",
      },
      {
        id: "registration-history",
        label: "Registration History",
        href: "/student/registration/history",
        icon: "history",
        figmaPage: "ST 04",
      },
    ],
  },
  {
    title: "TIMETABLE",
    icon: "calendar",
    items: [
      { id: "timetable", label: "Timetable Hub", href: "/student/timetable", icon: "calendar-days", figmaPage: "ST 05" },
      {
        id: "timetable-schedule",
        label: "Timetable",
        href: "/student/timetable/schedule",
        icon: "calendar-range",
        figmaPage: "ST 05",
      },
      { id: "semester-timetable", label: "Semester Timetable", href: "/student/timetable/semester", icon: "calendar", figmaPage: "ST 05" },
      { id: "academic-calendar", label: "Academic Calendar", href: "/student/timetable/calendar", icon: "calendar-check", figmaPage: "ST 05" },
      { id: "calendar-deadlines", label: "Calendar Deadlines", href: "/student/timetable/deadlines", icon: "alarm-clock", figmaPage: "ST 05" },
      { id: "examination-schedule", label: "Examination Schedule", href: "/student/timetable/examinations", icon: "clipboard-list", figmaPage: "ST 05" },
      { id: "timetable-changes", label: "Timetable Changes", href: "/student/timetable/changes", icon: "refresh-cw", figmaPage: "ST 05" },
      { id: "timetable-notifications", label: "Timetable Notifications", href: "/student/timetable/notifications", icon: "bell", figmaPage: "ST 05" },
      { id: "cancelled-sessions", label: "Cancelled Sessions", href: "/student/timetable/cancelled-sessions", icon: "calendar-x", figmaPage: "ST 05" },
    ],
  },
  {
    title: "ATTENDANCE",
    icon: "calendar-check",
    items: [
      { id: "attendance", label: "Attendance Overview", href: "/student/attendance", icon: "chart-pie", figmaPage: "ST 06" },
      { id: "attendance-subjects", label: "Subject Attendance", href: "/student/attendance/subjects", icon: "book-open", figmaPage: "ST 06" },
      { id: "attendance-daily", label: "Daily Attendance", href: "/student/attendance/daily", icon: "calendar-days", figmaPage: "ST 06" },
      { id: "attendance-history", label: "Attendance History", href: "/student/attendance/history", icon: "history", figmaPage: "ST 06" },
      { id: "attendance-shortages", label: "Shortage Tracking", href: "/student/attendance/shortages", icon: "triangle-alert", figmaPage: "ST 06" },
      { id: "attendance-eligibility", label: "Attendance Eligibility", href: "/student/attendance/eligibility", icon: "badge-check", figmaPage: "ST 06" },
      { id: "attendance-export", label: "Export Summary", href: "/student/attendance/export", icon: "download", figmaPage: "ST 06" },
      { id: "discrepancy-requests", label: "Discrepancy Requests", href: "/student/attendance/discrepancy-requests", icon: "file-warning", figmaPage: "ST 06" },
      { id: "new-discrepancy-request", label: "New Discrepancy", href: "/student/attendance/new-discrepancy", icon: "file-plus", figmaPage: "ST 06" },
    ],
  },
  {
    title: "CIA MARKS",
    icon: "clipboard-list",
    items: [
      { id: "cia", label: "CIA Overview", href: "/student/cia", icon: "layout-dashboard", figmaPage: "ST 07" },
      { id: "cia-schedules", label: "CIA Schedules", href: "/student/cia/schedules", icon: "calendar-clock", figmaPage: "ST 07" },
      { id: "cia-marks", label: "Published Marks", href: "/student/cia/marks", icon: "award", figmaPage: "ST 07" },
      { id: "cia-subject-marks", label: "Subject Marks", href: "/student/cia/subject-marks", icon: "chart-bar", figmaPage: "ST 07" },
      { id: "cia-corrections", label: "Corrections", href: "/student/cia/corrections", icon: "file-pen", figmaPage: "ST 07" },
      { id: "cia-history", label: "Marks History", href: "/student/cia/history", icon: "history", figmaPage: "ST 07" },
      { id: "cia-components", label: "Components", href: "/student/cia/components", icon: "layers", figmaPage: "ST 07" },
    ],
  },
  {
    title: "ASSESSMENTS",
    icon: "file-text",
    items: [
      { id: "assessments", label: "Assessment Hub", href: "/student/assessments", icon: "layout-list", figmaPage: "ST 08" },
      { id: "assignments", label: "Assignments", href: "/student/assessments/assignments", icon: "file-text", figmaPage: "ST 08" },
      { id: "assignment-detail", label: "Assignment Detail", href: "/student/assessments/assignment-detail", icon: "file-search", figmaPage: "ST 08" },
      { id: "quiz-schedules", label: "Quiz Schedules", href: "/student/assessments/quiz-schedules", icon: "timer", figmaPage: "ST 08" },
      { id: "quiz-results", label: "Quiz Results", href: "/student/assessments/quiz-results", icon: "list-checks", figmaPage: "ST 08" },
      { id: "assignment-marks", label: "Assignment Marks", href: "/student/assessments/marks", icon: "percent", figmaPage: "ST 08" },
      { id: "submission-status", label: "Submission Status", href: "/student/assessments/submission-status", icon: "upload", figmaPage: "ST 08" },
      { id: "assignment-feedback", label: "Feedback", href: "/student/assessments/feedback", icon: "message-square", figmaPage: "ST 08" },
      { id: "resubmission-eligibility", label: "Resubmission", href: "/student/assessments/resubmission", icon: "rotate-ccw", figmaPage: "ST 08" },
    ],
  },
];

export const studentNavFlat = studentNavGroups.flatMap((g) => g.items);

export function studentNavItemByHref(href: string): StudentNavItem | undefined {
  return studentNavFlat.find((item) => item.href === href);
}