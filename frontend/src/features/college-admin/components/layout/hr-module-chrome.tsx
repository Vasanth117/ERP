"use client";

import type { ReactNode } from "react";

import { CollegeAdminSectionChrome } from "@/features/college-admin/components/layout/college-admin-section-chrome";
import type { CollegeAdminTab } from "@/features/college-admin/config/section-tabs";
import { hrSectionTabs } from "@/features/college-admin/config/hr-section-tabs";

const hrModuleTabs = hrSectionTabs as CollegeAdminTab[];
const HR_LANDING_HREF =
  hrModuleTabs[0]?.href ?? "/college-admin/hr/hr-dashboard";

export function HrModuleChrome({ children }: { children: ReactNode }) {
  return (
    <CollegeAdminSectionChrome
      moduleTitle="Human Resources"
      moduleDescriptionLines={[
        "Employee records, recruitment and onboarding, attendance and leave,",
        "payroll, benefits, performance, and HR reporting.",
      ]}
      landingHref={HR_LANDING_HREF}
      tabs={hrModuleTabs}
    >
      {children}
    </CollegeAdminSectionChrome>
  );
}