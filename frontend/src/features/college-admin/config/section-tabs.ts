export type CollegeAdminTab = {
  label: string;
  href: string;
  figmaFrame: string;
};

/** Figma CA 01 — dashboard module tabs */
export const dashboardTabs: CollegeAdminTab[] = [
  {
    label: "Overview",
    href: "/college-admin/dashboard",
    figmaFrame: "64:190",
  },
  {
    label: "Institution",
    href: "/college-admin/dashboard/institutional-overview",
    figmaFrame: "65:185",
  },
  {
    label: "Students",
    href: "/college-admin/dashboard/student-statistics",
    figmaFrame: "65:618",
  },
  {
    label: "Faculty",
    href: "/college-admin/dashboard/faculty-statistics",
    figmaFrame: "65:1116",
  },
  {
    label: "Departments",
    href: "/college-admin/dashboard/department-performance",
    figmaFrame: "65:1592",
  },
  {
    label: "Academics",
    href: "/college-admin/dashboard/academic-analytics",
    figmaFrame: "66:1973",
  },
  {
    label: "Attendance",
    href: "/college-admin/dashboard/attendance-overview",
    figmaFrame: "66:2485",
  },
  {
    label: "Exams",
    href: "/college-admin/dashboard/examination-overview",
    figmaFrame: "66:2970",
  },
  {
    label: "Finance",
    href: "/college-admin/dashboard/finance-summary",
    figmaFrame: "66:3440",
  },
  {
    label: "Approvals",
    href: "/college-admin/dashboard/pending-approvals",
    figmaFrame: "67:3905",
  },
  {
    label: "Activities",
    href: "/college-admin/dashboard/recent-activities",
    figmaFrame: "67:4394",
  },
  {
    label: "Alerts",
    href: "/college-admin/dashboard/alerts",
    figmaFrame: "67:4882",
  },
];

/** Figma CA 02 — institution & campus settings */
export const institutionTabs: CollegeAdminTab[] = [
  {
    label: "Profile",
    href: "/college-admin/institution/profile",
    figmaFrame: "72:5933",
  },
  {
    label: "Information",
    href: "/college-admin/institution/information",
    figmaFrame: "72:6332",
  },
  {
    label: "Branding",
    href: "/college-admin/institution/branding",
    figmaFrame: "72:6775",
  },
  {
    label: "Campuses",
    href: "/college-admin/institution/campuses",
    figmaFrame: "72:7199",
  },
  {
    label: "Academic",
    href: "/college-admin/institution/academic-settings",
    figmaFrame: "72:8395",
  },
  {
    label: "Policies",
    href: "/college-admin/institution/policies",
    figmaFrame: "72:8805",
  },
  {
    label: "Academic year",
    href: "/college-admin/institution/academic-year",
    figmaFrame: "72:9235",
  },
  {
    label: "Calendar",
    href: "/college-admin/institution/calendar",
    figmaFrame: "72:9653",
  },
  {
    label: "History",
    href: "/college-admin/institution/configuration-history",
    figmaFrame: "72:10042",
  },
];

export function resolveSectionTabs(
  pathname: string,
): { section: string; tabs: CollegeAdminTab[] } | null {
  if (pathname.startsWith("/college-admin/dashboard")) {
    return { section: "Dashboard", tabs: dashboardTabs };
  }
  if (pathname.startsWith("/college-admin/institution")) {
    return { section: "Institution", tabs: institutionTabs };
  }
  if (pathname.startsWith("/college-admin/users")) {
    return null;
  }
  if (pathname.startsWith("/college-admin/organization")) {
    return null;
  }
  return null;
}