"use client";

import type { ReactNode } from "react";

import { CollegeAdminPageTabs } from "@/features/college-admin/components/layout/college-admin-page-tabs";
import { academicsTabs } from "@/features/college-admin/config/academics-section-tabs";

export function AcademicsModuleChrome({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto w-full max-w-[1440px]">
      <header className="mb-5">
        <h1 className="text-[26px] font-bold leading-tight tracking-[-0.02em] text-[#111827]">
          Academics
        </h1>
        <p className="mt-2 max-w-3xl text-[14px] leading-relaxed text-[#6b7280]">
          Academic years, programmes, curriculum, grading rules, and configuration history for your institution.
        </p>
      </header>

      <CollegeAdminPageTabs tabs={academicsTabs} className="mb-8" />

      {children}
    </div>
  );
}