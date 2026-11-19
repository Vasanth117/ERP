export type CollegeAdminNavItem = {
  id: string;
  label: string;
  href: string;
  icon: string;
  figmaPage?: string;
};

export type CollegeAdminNavGroup = {
  title: string;
  items: CollegeAdminNavItem[];
};

export const collegeAdminNavGroups: CollegeAdminNavGroup[] = [
  {
    title: "OVERVIEW",
    items: [
      {
        id: "dashboard",
        label: "Dashboard",
        href: "/college-admin/dashboard",
        icon: "3e5bc",
        figmaPage: "CA 01",
      },
    ],
  },
  {
    title: "INSTITUTION",
    items: [
      {
        id: "institution",
        label: "Institution",
        href: "/college-admin/institution/profile",
        icon: "de8b2",
        figmaPage: "CA 02",
      },
      {
        id: "users",
        label: "Users & Permissions",
        href: "/college-admin/users/user-management-dashboard",
        icon: "c9306",
        figmaPage: "CA 03",
      },
      {
        id: "organization",
        label: "Organization",
        href: "/college-admin/organization/department-management-dashboard",
        icon: "181e9",
        figmaPage: "CA 04",
      },
    ],
  },
  {
    title: "ACADEMICS",
    items: [
      {
        id: "academics",
        label: "Academics",
        href: "/college-admin/academics/academic-configuration-dashboard",
        icon: "f5b42",
        figmaPage: "CA 05",
      },
      {
        id: "students",
        label: "Students",
        href: "/college-admin/students/student-administration-dashboard",
        icon: "eb36a",
        figmaPage: "CA 06",
      },
      {
        id: "faculty",
        label: "Faculty & Employees",
        href: "/college-admin/faculty/faculty-employee-dashboard",
        icon: "629af",
        figmaPage: "CA 07",
      },
      {
        id: "attendance",
        label: "Attendance",
        href: "/college-admin/attendance/attendance-dashboard",
        icon: "a1df0",
        figmaPage: "CA 08",
      },
      {
        id: "examinations",
        label: "Examinations",
        href: "/college-admin/examinations/examination-dashboard",
        icon: "48683",
        figmaPage: "CA 09",
      },
      {
        id: "lms",
        label: "Learning Management",
        href: "/college-admin/lms/lms-dashboard",
        icon: "e15fc",
        figmaPage: "CA 15",
      },
    ],
  },
  {
    title: "ADMINISTRATION",
    items: [
      {
        id: "finance",
        label: "Finance",
        href: "/college-admin/finance/finance-dashboard",
        icon: "f21fe",
        figmaPage: "CA 10",
      },
      {
        id: "hr",
        label: "Human Resources",
        href: "/college-admin/hr/hr-dashboard",
        icon: "53516",
        figmaPage: "CA 11",
      },
      {
        id: "library",
        label: "Library",
        href: "/college-admin/library/library-dashboard",
        icon: "812ba",
        figmaPage: "CA 12",
      },
      {
        id: "hostel",
        label: "Hostel",
        href: "/college-admin/hostel/hostel-dashboard",
        icon: "a4dde",
        figmaPage: "CA 13",
      },
      {
        id: "communication",
        label: "Communication",
        href: "/college-admin/communication/communication-dashboard",
        icon: "da97a",
        figmaPage: "CA 14",
      },
    ],
  },
  {
    title: "GOVERNANCE",
    items: [
      {
        id: "reports",
        label: "Reports & Analytics",
        href: "/college-admin/reports/analytics-dashboard",
        icon: "a8dc1",
        figmaPage: "CA 16",
      },
      {
        id: "approvals",
        label: "Approvals",
        href: "/college-admin/approvals/approvals-dashboard",
        icon: "ee32f",
        figmaPage: "CA 17",
      },
      {
        id: "security",
        label: "Security & Audit",
        href: "/college-admin/security/security-dashboard",
        icon: "a75fd",
        figmaPage: "CA 18",
      },
      {
        id: "data",
        label: "Data Management",
        href: "/college-admin/data-import/import-dashboard",
        icon: "46882",
        figmaPage: "CA 19",
      },
      {
        id: "integrations",
        label: "Integrations",
        href: "/college-admin/integrations/integrations-dashboard",
        icon: "495b3",
        figmaPage: "CA 20",
      },
      {
        id: "helpdesk",
        label: "Helpdesk",
        href: "/college-admin/helpdesk/helpdesk-dashboard",
        icon: "09b1d",
        figmaPage: "CA 21",
      },
    ],
  },
  {
    title: "EXTENSIONS",
    items: [
      {
        id: "finance-ext",
        label: "Finance Extensions",
        href: "/college-admin/finance-extensions/finance-extensions-dashboard",
        icon: "1433e",
        figmaPage: "CA 22",
      },
      {
        id: "operations",
        label: "Operations",
        href: "/college-admin/operations/operations-dashboard",
        icon: "bcb49",
        figmaPage: "CA 23",
      },
    ],
  },
];