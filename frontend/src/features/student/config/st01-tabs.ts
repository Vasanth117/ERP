import type { CollegeAdminTab } from "@/features/college-admin/config/section-tabs";

/** Figma ST 01 — module tabs (node 164:227). */
export const studentSt01Tabs: CollegeAdminTab[] = [
  {
    label: "Dashboard",
    href: "/student/dashboard",
    figmaFrame: "164:228",
  },
  {
    label: "Profile",
    href: "/student/profile",
    figmaFrame: "164:230",
  },
  {
    label: "Update requests",
    href: "/student/profile/update-requests",
    figmaFrame: "164:232",
  },
  {
    label: "Documents",
    href: "/student/documents",
    figmaFrame: "164:234",
  },
];

const ST01_PATHS = studentSt01Tabs.map((t) => t.href);

export function isStudentSt01Path(pathname: string): boolean {
  if (pathname === "/student/profile/activity") return true;
  return ST01_PATHS.some(
    (p) => pathname === p || (p !== "/student/dashboard" && pathname.startsWith(`${p}/`)),
  );
}

export function studentSt01BreadcrumbLeaf(pathname: string): string {
  if (pathname === "/student/dashboard") return "Main Student Dashboard";
  if (pathname === "/student/profile") return "Student Profile Overview";
  if (pathname === "/student/profile/personal") return "Personal information";
  if (pathname === "/student/profile/academic") return "Academic profile";
  if (pathname === "/student/profile/contact") return "Contact information";
  if (pathname === "/student/profile/guardian") return "Guardian information";
  if (pathname === "/student/profile/edit") return "Edit permitted profile details";
  if (pathname.startsWith("/student/profile/update-requests")) return "Update requests";
  if (pathname.startsWith("/student/documents")) return "Student Documents Overview";
  if (pathname.startsWith("/student/profile/activity")) return "Profile activity";
  return "Student";
}