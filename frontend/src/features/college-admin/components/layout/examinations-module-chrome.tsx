"use client";

import type { ReactNode } from "react";

import { CollegeAdminSectionChrome } from "@/features/college-admin/components/layout/college-admin-section-chrome";
import { examinationsTabs } from "@/features/college-admin/config/section-tabs";

export function ExaminationsModuleChrome({ children }: { children: ReactNode }) {
  return (
    <CollegeAdminSectionChrome
      moduleTitle="Examinations"
      landingHref={examinationsTabs[0]!.href}
      tabs={examinationsTabs}
    >
      {children}
    </CollegeAdminSectionChrome>
  );
}