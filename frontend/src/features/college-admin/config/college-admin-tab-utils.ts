import type { CollegeAdminTab } from "@/features/college-admin/config/section-tabs";

export function isCollegeAdminTabActive(pathname: string, tab: CollegeAdminTab): boolean {
  const { href, activePrefixes } = tab;
  if (activePrefixes?.length) {
    return activePrefixes.some(
      (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
    );
  }
  if (href === "/college-admin/dashboard") {
    return pathname === href;
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}