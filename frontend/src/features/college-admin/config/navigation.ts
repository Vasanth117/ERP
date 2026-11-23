import type { ErpIconName } from "@/components/icons/erp/names";

export type CollegeAdminNavItem = {
  id: string;
  label: string;
  href: string;
  /** ERP icon library slug (`components/icons/erp/generated`). */
  icon: ErpIconName;
  figmaPage?: string;
  /** Child routes that belong to this sidebar item (defaults to same module segment). */
  activePrefixes?: string[];
};

export type CollegeAdminNavGroup = {
  title: string;
  icon: ErpIconName;
  items: CollegeAdminNavItem[];
};

export const collegeAdminNavGroups: CollegeAdminNavGroup[] = [
  {
    title: "OVERVIEW",
    icon: "panels-top-left",
    items: [
      {
        id: "dashboard",
        label: "Dashboard",
        href: "/college-admin/dashboard",
        icon: "layout-dashboard",
        figmaPage: "CA 01",
      },
    ],
  },
  {
    title: "INSTITUTION",
    icon: "landmark",
    items: [
      {
        id: "institution",
        label: "Institution",
        href: "/college-admin/institution/profile",
        icon: "building-2",
        figmaPage: "CA 02",
      },
      {
        id: "users",
        label: "Users & Permissions",
        href: "/college-admin/users/user-management-dashboard",
        icon: "user-cog",
        figmaPage: "CA 03",
      },
      {
        id: "organization",
        label: "Organization",
        href: "/college-admin/organization/department-management-dashboard",
        icon: "network",
        figmaPage: "CA 04",
      },
    ],
  },
  {
    title: "ACADEMICS",
    icon: "book-open",
    items: [
      {
        id: "academics",
        label: "Academics",
        href: "/college-admin/academics/academic-configuration-dashboard",
        icon: "book-open",
        figmaPage: "CA 05",
      },
      {
        id: "students",
        label: "Students",
        href: "/college-admin/students/student-administration-dashboard",
        icon: "graduation-cap",
        figmaPage: "CA 06",
      },
      {
        id: "faculty",
        label: "Faculty & Employees",
        href: "/college-admin/faculty/faculty-employee-dashboard",
        icon: "id-card",
        figmaPage: "CA 07",
      },
      {
        id: "attendance",
        label: "Attendance",
        href: "/college-admin/attendance/attendance-dashboard",
        icon: "calendar-check",
        figmaPage: "CA 08",
      },
      {
        id: "examinations",
        label: "Examinations",
        href: "/college-admin/examinations/examination-dashboard",
        icon: "clipboard-list",
        figmaPage: "CA 09",
      },
      {
        id: "lms",
        label: "Learning Management",
        href: "/college-admin/lms/lms-dashboard",
        icon: "monitor-play",
        figmaPage: "CA 15",
      },
    ],
  },
  {
    title: "ADMINISTRATION",
    icon: "user-round-cog",
    items: [
      {
        id: "finance",
        label: "Finance",
        href: "/college-admin/finance/finance-dashboard",
        icon: "wallet",
        figmaPage: "CA 10",
      },
      {
        id: "hr",
        label: "Human Resources",
        href: "/college-admin/hr/hr-dashboard",
        icon: "contact",
        figmaPage: "CA 11",
      },
      {
        id: "library",
        label: "Library",
        href: "/college-admin/library/library-dashboard",
        icon: "library-big",
        figmaPage: "CA 12",
      },
      {
        id: "hostel",
        label: "Hostel",
        href: "/college-admin/hostel/hostel-dashboard",
        icon: "hotel",
        figmaPage: "CA 13",
      },
      {
        id: "communication",
        label: "Communication",
        href: "/college-admin/communication/communication-dashboard",
        icon: "message-square",
        figmaPage: "CA 14",
      },
    ],
  },
  {
    title: "GOVERNANCE",
    icon: "shield",
    items: [
      {
        id: "reports",
        label: "Reports & Analytics",
        href: "/college-admin/reports/reports-dashboard",
        icon: "chart-bar",
        figmaPage: "CA 16",
      },
      {
        id: "approvals",
        label: "Approvals",
        href: "/college-admin/approvals/approval-dashboard",
        icon: "square-check",
        figmaPage: "CA 17",
      },
      {
        id: "security",
        label: "Security & Audit",
        href: "/college-admin/security/security-dashboard",
        icon: "shield-check",
        figmaPage: "CA 18",
      },
      {
        id: "data",
        label: "Data Management",
        href: "/college-admin/data-import/data-management-dashboard",
        icon: "database",
        figmaPage: "CA 19",
      },
      {
        id: "integrations",
        label: "Integrations",
        href: "/college-admin/integrations/integration-dashboard",
        icon: "plug",
        figmaPage: "CA 20",
      },
      {
        id: "helpdesk",
        label: "Helpdesk",
        href: "/college-admin/helpdesk/helpdesk-dashboard",
        icon: "life-buoy",
        figmaPage: "CA 21",
      },
    ],
  },
  {
    title: "EXTENSIONS",
    icon: "sliders-horizontal",
    items: [
      {
        id: "finance-ext",
        label: "Finance Extensions",
        href: "/college-admin/finance-extensions/institutional-finance-dashboard",
        icon: "receipt",
        figmaPage: "CA 22",
      },
      {
        id: "operations",
        label: "Operations",
        href: "/college-admin/operations/operations-dashboard",
        icon: "wrench",
        figmaPage: "CA 23",
      },
    ],
  },
];