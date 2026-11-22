"use client";

import type { ReactNode } from "react";

import { CollegeAdminSectionChrome } from "@/features/college-admin/components/layout/college-admin-section-chrome";
import { organizationTabs } from "@/features/college-admin/config/section-tabs";

export function OrganizationModuleChrome({ children }: { children: ReactNode }) {
  return (
    <CollegeAdminSectionChrome
      moduleTitle="Organization"
      moduleDescription="Departments, hierarchy, programmes, and faculty allocation across your institution."
      landingHref={organizationTabs[0]!.href}
      tabs={organizationTabs}
    >
      {children}
    </CollegeAdminSectionChrome>
  );
}