"use client";

import { CollegeAdminSectionNav } from "@/features/college-admin/components/ui/college-admin-section-nav";
import type { ExaminationRegistrationSubNavItem } from "@/features/college-admin/types/examination-registration-shared";

export function ExaminationRegistrationSubNav({ items }: { items: ExaminationRegistrationSubNavItem[] }) {
  return (
    <CollegeAdminSectionNav
      items={items.map(({ key, label, href, active }) => ({ key, label, href, active }))}
    />
  );
}