export type LandingModule = {
  id: string;
  title: string;
  description: string;
  icon: string;
  variant?: "default" | "featured";
};

const moduleLoginTargets: Record<string, { portal: string; next: string }> = {
  institution: {
    portal: "institution",
    next: "/college-admin/dashboard",
  },
  "student-academic": {
    portal: "student-performance",
    next: "/student/home",
  },
  performance: {
    portal: "student-performance",
    next: "/student/home",
  },
};

/** Module cards route to module login when a workspace exists; otherwise under construction. */
export function landingModuleHref(moduleId: string): string {
  const login = moduleLoginTargets[moduleId];
  if (login) {
    const params = new URLSearchParams({
      portal: login.portal,
      next: login.next,
    });
    return `/login?${params.toString()}`;
  }
  return `/under-construction?module=${encodeURIComponent(moduleId)}`;
}

/** Figma frame 338:279 — module grid + System Control & Security. */
export const landingModules: LandingModule[] = [
  {
    id: "institution",
    title: "Institution Management",
    description:
      "Manage college profile, campuses, departments, institutional settings and user permissions.",
    icon: "/landing/06450.png",
  },
  {
    id: "admission",
    title: "Admission Management",
    description:
      "Manage applications, applicant verification, admission processes and enrollment.",
    icon: "/landing/2be02.png",
  },
  {
    id: "student-academic",
    title: "Student Academic",
    description:
      "Manage student records, courses, curriculum, attendance and academic progress.",
    icon: "/landing/40b31.png",
  },
  {
    id: "hostel",
    title: "Hostel & Mess",
    description:
      "Manage hostel buildings, rooms, residents, mess, visitors and outpass operations.",
    icon: "/landing/18ec3.png",
  },
  {
    id: "billing",
    title: "Billing & Fees",
    description:
      "Manage fee structures, student invoices, collections, concessions and outstanding dues.",
    icon: "/landing/c12b9.png",
  },
  {
    id: "faculty",
    title: "Staff & Faculty Academic",
    description:
      "Manage faculty profiles, workload, subject allocation and teaching responsibilities.",
    icon: "/landing/f3bcb.png",
  },
  {
    id: "inventory",
    title: "Stock & Inventory",
    description:
      "Manage institutional assets, stock, equipment, goods, transfers and stock verification.",
    icon: "/landing/e2704.png",
  },
  {
    id: "finance",
    title: "Finance & Accounting",
    description:
      "Manage accounts, ledgers, budgets, vendors, expenses and financial reports.",
    icon: "/landing/8ed81.png",
  },
  {
    id: "hr",
    title: "HR & Payroll",
    description:
      "Manage employees, recruitment, leave, attendance, salary and payroll processing.",
    icon: "/landing/2486e.png",
  },
  {
    id: "mis",
    title: "MIS Reports & Analytics",
    description:
      "View institutional reports, academic performance, financial statistics and operational analytics.",
    icon: "/landing/0ad86.png",
  },
  {
    id: "messaging",
    title: "Messaging & Notifications",
    description:
      "Send announcements, SMS, email and notifications to students, parents and staff.",
    icon: "/landing/ff7cf.png",
  },
  {
    id: "library",
    title: "Library Management",
    description:
      "Manage books, catalogue, inventory, issue, return, reservations and digital resources.",
    icon: "/landing/a675c.png",
  },
  {
    id: "performance",
    title: "Student Performance",
    description:
      "Track attendance, internal marks, examination results, GPA, CGPA and student progress.",
    icon: "/landing/308d6.png",
  },
  {
    id: "office",
    title: "Office & Administration",
    description:
      "Manage office workflows, certificates, student requests, tasks and administrative activities.",
    icon: "/landing/b8e39.png",
  },
  {
    id: "staff-workspace",
    title: "Staff Workspace",
    description:
      "Access employee self-service, assigned tasks, leave requests and personal work information.",
    icon: "/landing/d8ed6.png",
  },
  {
    id: "transport",
    title: "Transport Management",
    description:
      "Manage routes, vehicles, drivers, student allocations and transport fees.",
    icon: "/landing/2e548.png",
  },
  {
    id: "examination",
    title: "Examination Management",
    description:
      "Manage exam sessions, timetables, hall tickets, marks, results and revaluation.",
    icon: "/landing/8f5d1.png",
  },
  {
    id: "calendar",
    title: "Calendar & Events",
    description:
      "Manage academic calendars, holidays, events, examinations and institutional schedules.",
    icon: "/landing/c9589.png",
  },
  {
    id: "campus-ops",
    title: "Campus Operations",
    description:
      "Manage facilities, maintenance requests, visitors, complaints and campus services.",
    icon: "/landing/e00e1.png",
  },
  {
    id: "other",
    title: "Other ERP Modules",
    description:
      "Discover additional enabled modules, integrations and institutional services.",
    icon: "/landing/39783.png",
  },
  {
    id: "system-control",
    title: "System Control & Security",
    description:
      "Manage system settings, access policies, audit logs, integrations and system health.",
    icon: "/landing/bfb04.png",
    variant: "featured",
  },
];
