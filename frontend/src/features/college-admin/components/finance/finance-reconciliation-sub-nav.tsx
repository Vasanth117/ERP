"use client";

import { CollegeAdminSectionNav } from "@/features/college-admin/components/ui/college-admin-section-nav";
import type { FinanceReconciliationSubNavItem } from "@/features/college-admin/types/finance-reconciliation-shared";

export function FinanceReconciliationSubNav({ items }: { items: FinanceReconciliationSubNavItem[] }) {
  return (
    <CollegeAdminSectionNav
      items={items.map(({ key, label, href, active }) => ({ key, label, href, active }))}
    />
  );
}