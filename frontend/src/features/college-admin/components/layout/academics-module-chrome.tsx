"use client";

import type { ReactNode } from "react";

import { CollegeAdminSectionChrome } from "@/features/college-admin/components/layout/college-admin-section-chrome";
import { academicsTabs } from "@/features/college-admin/config/section-tabs";

export function AcademicsModuleChrome({ children }: { children: ReactNode }) {
  return (
    <CollegeAdminSectionChrome
      moduleTitle="Academics"
      landingHref={academicsTabs[0]!.href}
      tabs={academicsTabs}
    >
      {children}
    </CollegeAdminSectionChrome>
  );
}