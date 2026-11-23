import type { CollegeAdminNavItem } from "@/features/college-admin/config/navigation";

export function normalizeCollegeAdminPathname(pathname: string): string {
  if (pathname.length > 1 && pathname.endsWith("/")) {
    return pathname.slice(0, -1);
  }
  return pathname;
}

/** First URL segment after `/college-admin/` (e.g. `academics`, `students`). */
export function collegeAdminModuleKey(path: string): string | null {
  const match = normalizeCollegeAdminPathname(path).match(/^\/college-admin\/([^/]+)/);
  return match?.[1] ?? null;
}

export function isCollegeAdminNavItemActive(
  pathname: string,
  item: CollegeAdminNavItem,
): boolean {
  const path = normalizeCollegeAdminPathname(pathname);
  const { href, activePrefixes } = item;

  if (activePrefixes?.length) {
    return activePrefixes.some(
      (prefix) => path === prefix || path.startsWith(`${prefix}/`),
    );
  }

  if (path === href || path.startsWith(`${href}/`)) {
    return true;
  }

  if (href === "/college-admin/dashboard") {
    return path === "/college-admin" || path.startsWith(`${href}/`);
  }

  const itemModule = collegeAdminModuleKey(href);
  const pathModule = collegeAdminModuleKey(path);
  if (itemModule && pathModule && itemModule === pathModule) {
    return true;
  }

  return false;
}