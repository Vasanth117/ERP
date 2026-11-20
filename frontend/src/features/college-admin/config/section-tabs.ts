export type CollegeAdminTab = {
  label: string;
  href: string;
  figmaFrame: string;
  /** Extra path prefixes that should keep this tab highlighted (e.g. detail routes). */
  activePrefixes?: string[];
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

/** Figma CA 03 — users & permissions (section nav only; not every screen). */
export const usersTabs: CollegeAdminTab[] = [
  {
    label: "Users",
    href: "/college-admin/users/user-management-dashboard",
    figmaFrame: "69:124928",
    activePrefixes: [
      "/college-admin/users/all-users-list",
      "/college-admin/users/user-management-dashboard",
      "/college-admin/users/user-details",
      "/college-admin/users/edit-user-information",
    ],
  },
  {
    label: "Create & invite",
    href: "/college-admin/users/create-new-user",
    figmaFrame: "69:125683",
    activePrefixes: [
      "/college-admin/users/create-new-user",
      "/college-admin/users/bulk-user-invitation",
    ],
  },
  {
    label: "Roles",
    href: "/college-admin/users/role-management-dashboard",
    figmaFrame: "69:126349",
    activePrefixes: [
      "/college-admin/users/role-management-dashboard",
      "/college-admin/users/create-edit-role",
      "/college-admin/users/role-assignment",
    ],
  },
  {
    label: "Permissions",
    href: "/college-admin/users/permission-management",
    figmaFrame: "69:126902",
  },
  {
    label: "Account status",
    href: "/college-admin/users/user-account-activation-suspension",
    figmaFrame: "69:127501",
  },
  {
    label: "Activity",
    href: "/college-admin/users/login-account-activity",
    figmaFrame: "69:127724",
    activePrefixes: [
      "/college-admin/users/login-account-activity",
      "/college-admin/users/user-access-history",
    ],
  },
];

/** Figma CA 04 — organization & departments (section nav; detail routes use activePrefixes). */
export const organizationTabs: CollegeAdminTab[] = [
  {
    label: "Departments",
    href: "/college-admin/organization/department-management-dashboard",
    figmaFrame: "69:132597",
    activePrefixes: [
      "/college-admin/organization/department-management-dashboard",
      "/college-admin/organization/all-departments",
    ],
  },
  {
    label: "Create & edit",
    href: "/college-admin/organization/create-department",
    figmaFrame: "69:133115",
    activePrefixes: [
      "/college-admin/organization/create-department",
      "/college-admin/organization/department-edit",
      "/college-admin/organization/department-details",
    ],
  },
  {
    label: "Heads",
    href: "/college-admin/organization/department-head-assignment",
    figmaFrame: "69:133798",
  },
  {
    label: "Hierarchy",
    href: "/college-admin/organization/organizational-hierarchy",
    figmaFrame: "69:134048",
  },
  {
    label: "Programmes",
    href: "/college-admin/organization/programme-course-mapping",
    figmaFrame: "69:134275",
  },
  {
    label: "Faculty & resources",
    href: "/college-admin/organization/department-faculty-allocation",
    figmaFrame: "69:134506",
    activePrefixes: [
      "/college-admin/organization/department-faculty-allocation",
      "/college-admin/organization/department-resource-management",
    ],
  },
  {
    label: "History",
    href: "/college-admin/organization/department-status-history",
    figmaFrame: "69:135016",
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
    return { section: "Users & Permissions", tabs: usersTabs };
  }
  if (pathname.startsWith("/college-admin/organization")) {
    return { section: "Organization", tabs: organizationTabs };
  }
  return null;
}