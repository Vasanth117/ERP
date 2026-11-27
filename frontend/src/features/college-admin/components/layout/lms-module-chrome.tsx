"use client";

import type { ReactNode } from "react";

import { CollegeAdminSectionChrome } from "@/features/college-admin/components/layout/college-admin-section-chrome";
import type { CollegeAdminTab } from "@/features/college-admin/config/section-tabs";
import { lmsSectionTabs } from "@/features/college-admin/config/lms-section-tabs";

const lmsModuleTabs = lmsSectionTabs as CollegeAdminTab[];
const LMS_LANDING_HREF = lmsModuleTabs[0]?.href ?? "/college-admin/lms/lms-dashboard";

export function LmsModuleChrome({ children }: { children: ReactNode }) {
  return (
    <CollegeAdminSectionChrome
      moduleTitle="Learning Management"
      landingHref={LMS_LANDING_HREF}
      tabs={lmsModuleTabs}
    >
      {children}
    </CollegeAdminSectionChrome>
  );
}