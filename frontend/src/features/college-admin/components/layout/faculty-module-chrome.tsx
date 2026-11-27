"use client";

import type { ReactNode } from "react";

import { CollegeAdminSectionChrome } from "@/features/college-admin/components/layout/college-admin-section-chrome";
import { facultyTabs } from "@/features/college-admin/config/section-tabs";

export function FacultyModuleChrome({ children }: { children: ReactNode }) {
  return (
    <CollegeAdminSectionChrome
      moduleTitle="Faculty & Employees"
      landingHref={facultyTabs[0]!.href}
      tabs={facultyTabs}
    >
      {children}
    </CollegeAdminSectionChrome>
  );
}