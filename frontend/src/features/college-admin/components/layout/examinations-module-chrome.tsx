"use client";

import type { ReactNode } from "react";

import { CollegeAdminPageTabs } from "@/features/college-admin/components/layout/college-admin-page-tabs";
import { examinationsTabs } from "@/features/college-admin/config/section-tabs";

export function ExaminationsModuleChrome({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto w-full max-w-[1440px]">
      <header className="mb-5">
        <h1 className="text-[26px] font-bold leading-tight tracking-[-0.02em] text-[#111827]">
          Examinations
        </h1>
        <p className="mt-2 max-w-3xl text-[14px] leading-relaxed text-[#6b7280]">
          Session setup, registration, halls, marks entry, results and reporting for your institution.
        </p>
      </header>

      <CollegeAdminPageTabs tabs={examinationsTabs} className="mb-8" />

      {children}
    </div>
  );
}