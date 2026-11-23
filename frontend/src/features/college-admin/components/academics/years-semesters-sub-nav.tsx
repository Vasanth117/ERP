"use client";

import { CollegeAdminSectionNav } from "@/features/college-admin/components/ui/college-admin-section-nav";
import type { YearsSemestersSubNavItem } from "@/features/college-admin/types/academic-year-management";

export function YearsSemestersSubNav({ items }: { items: YearsSemestersSubNavItem[] }) {
  return (
    <CollegeAdminSectionNav
      items={items.map(({ key, label, href, active }) => ({ key, label, href, active }))}
    />
  );
}