"use client";

import type { ReactNode } from "react";

import { CollegeAdminSectionChrome } from "@/features/college-admin/components/layout/college-admin-section-chrome";
import type { CollegeAdminTab } from "@/features/college-admin/config/section-tabs";
import { reportsSectionTabs } from "@/features/college-admin/config/reports-section-tabs";

const reportsModuleTabs = reportsSectionTabs as CollegeAdminTab[];
const REPORTS_LANDING_HREF = reportsModuleTabs[0]?.href ?? "/college-admin/reports/reports-dashboard";

export function ReportsModuleChrome({ children }: { children: ReactNode }) {
  return (
    <CollegeAdminSectionChrome
      moduleTitle="Reports & Analytics"
      landingHref={REPORTS_LANDING_HREF}
      tabs={reportsModuleTabs}
    >
      {children}
    </CollegeAdminSectionChrome>
  );
}