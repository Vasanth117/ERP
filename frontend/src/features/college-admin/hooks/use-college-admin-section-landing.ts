"use client";

import { usePathname } from "next/navigation";

import { resolveSectionTabs } from "@/features/college-admin/config/section-tabs";

/** True on a section’s Overview tab (first tab / landing URL). */
export function useCollegeAdminSectionLanding(): boolean {
  const pathname = usePathname() ?? "";
  const resolved = resolveSectionTabs(pathname);
  if (!resolved?.tabs.length) return false;
  return pathname === resolved.tabs[0]!.href;
}