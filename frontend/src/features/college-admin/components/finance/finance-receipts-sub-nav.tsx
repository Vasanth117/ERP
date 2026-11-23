"use client";

import { CollegeAdminSectionNav } from "@/features/college-admin/components/ui/college-admin-section-nav";
import type { FinanceReceiptsSubNavItem } from "@/features/college-admin/types/finance-receipts-shared";

export function FinanceReceiptsSubNav({ items }: { items: FinanceReceiptsSubNavItem[] }) {
  return (
    <CollegeAdminSectionNav
      items={items.map(({ key, label, href, active }) => ({ key, label, href, active }))}
    />
  );
}