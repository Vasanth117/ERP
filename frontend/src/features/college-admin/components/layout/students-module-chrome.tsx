"use client";

import type { ReactNode } from "react";

import { CollegeAdminSectionChrome } from "@/features/college-admin/components/layout/college-admin-section-chrome";
import { studentsTabs } from "@/features/college-admin/config/section-tabs";

export function StudentsModuleChrome({ children }: { children: ReactNode }) {
  return (
    <CollegeAdminSectionChrome
      moduleTitle="Students"
      landingHref={studentsTabs[0]!.href}
      tabs={studentsTabs}
    >
      {children}
    </CollegeAdminSectionChrome>
  );
}