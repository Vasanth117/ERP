import type { CollegeAdminTab } from "@/features/college-admin/config/section-tabs";
import { normalizeCollegeAdminPathname } from "@/features/college-admin/config/college-admin-nav-utils";

export function isCollegeAdminTabActive(pathname: string, tab: CollegeAdminTab): boolean {
  const path = normalizeCollegeAdminPathname(pathname);
  const { href, activePrefixes } = tab;
  if (activePrefixes?.length) {
    return activePrefixes.some(
      (prefix) => path === prefix || path.startsWith(`${prefix}/`),
    );
  }
  if (href === "/college-admin/dashboard") {
    return path === href;
  }
  return path === href || path.startsWith(`${href}/`);
}