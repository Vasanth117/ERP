"use client";

import type { ReactNode } from "react";

import { CollegeAdminSectionChrome } from "@/features/college-admin/components/layout/college-admin-section-chrome";
import { institutionTabs } from "@/features/college-admin/config/section-tabs";

export function InstitutionModuleChrome({ children }: { children: ReactNode }) {
  return (
    <CollegeAdminSectionChrome
      moduleTitle="Institution & campus"
      moduleDescription="Profile, branding, policies, and campus configuration for your college."
      landingHref={institutionTabs[0]!.href}
      tabs={institutionTabs}
    >
      {children}
    </CollegeAdminSectionChrome>
  );
}