"use client";

import type { ReactNode } from "react";

import { CollegeAdminSectionChrome } from "@/features/college-admin/components/layout/college-admin-section-chrome";
import { financeTabs } from "@/features/college-admin/config/section-tabs";

export function FinanceModuleChrome({ children }: { children: ReactNode }) {
  return (
    <CollegeAdminSectionChrome
      moduleTitle="Finance"
      landingHref={financeTabs[0]!.href}
      tabs={financeTabs}
    >
      {children}
    </CollegeAdminSectionChrome>
  );
}