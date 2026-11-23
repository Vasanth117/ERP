"use client";

import { CollegeAdminSectionNav } from "@/features/college-admin/components/ui/college-admin-section-nav";
import type { FinancePaymentsSubNavItem } from "@/features/college-admin/types/finance-payments-shared";

export function FinancePaymentsSubNav({ items }: { items: FinancePaymentsSubNavItem[] }) {
  return (
    <CollegeAdminSectionNav
      items={items.map(({ key, label, href, active }) => ({ key, label, href, active }))}
    />
  );
}