"use client";

import type { ReactNode } from "react";

import { CollegeAdminSectionChrome } from "@/features/college-admin/components/layout/college-admin-section-chrome";
import { dashboardTabs } from "@/features/college-admin/config/section-tabs";

export function DashboardModuleChrome({ children }: { children: ReactNode }) {
  return (
    <CollegeAdminSectionChrome
      moduleTitle="College Admin Dashboard"
      landingHref="/college-admin/dashboard"
      tabs={dashboardTabs}
    >
      {children}
    </CollegeAdminSectionChrome>
  );
}