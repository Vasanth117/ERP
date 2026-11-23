"use client";

import type { ReactNode } from "react";

import { CollegeAdminSectionChrome } from "@/features/college-admin/components/layout/college-admin-section-chrome";
import { attendanceTabs } from "@/features/college-admin/config/section-tabs";

export function AttendanceModuleChrome({ children }: { children: ReactNode }) {
  return (
    <CollegeAdminSectionChrome
      moduleTitle="Attendance"
      moduleDescription="Student and faculty attendance, submission monitoring, corrections, policies, and compliance reports."
      landingHref={attendanceTabs[0]!.href}
      tabs={attendanceTabs}
    >
      {children}
    </CollegeAdminSectionChrome>
  );
}