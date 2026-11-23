"use client";

import { CollegeAdminSectionNav } from "@/features/college-admin/components/ui/college-admin-section-nav";
import type { FinanceAidSubNavItem } from "@/features/college-admin/types/finance-aid-shared";

export function FinanceAidSubNav({ items }: { items: FinanceAidSubNavItem[] }) {
  return (
    <CollegeAdminSectionNav
      items={items.map(({ key, label, href, active }) => ({ key, label, href, active }))}
    />
  );
}