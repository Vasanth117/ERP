"use client";

import type { ReactNode } from "react";

import { CollegeAdminPageTabs } from "@/features/college-admin/components/layout/college-admin-page-tabs";
import { attendanceTabs } from "@/features/college-admin/config/section-tabs";

export function AttendanceModuleChrome({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto w-full max-w-[1440px]">
      <header className="mb-5">
        <h1 className="text-[26px] font-bold leading-tight tracking-[-0.02em] text-[#111827]">
          Attendance
        </h1>
        <p className="mt-2 max-w-3xl text-[14px] leading-relaxed text-[#6b7280]">
          Student and faculty attendance, submission monitoring, corrections, policies, and compliance reports.
        </p>
      </header>

      <CollegeAdminPageTabs tabs={attendanceTabs} className="mb-8" />

      {children}
    </div>
  );
}