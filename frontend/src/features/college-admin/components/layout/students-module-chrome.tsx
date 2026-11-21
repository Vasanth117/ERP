"use client";

import type { ReactNode } from "react";

import { CollegeAdminPageTabs } from "@/features/college-admin/components/layout/college-admin-page-tabs";
import { studentsTabs } from "@/features/college-admin/config/section-tabs";

export function StudentsModuleChrome({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto w-full max-w-[1440px]">
      <header className="mb-5">
        <h1 className="text-[26px] font-bold leading-tight tracking-[-0.02em] text-[#111827]">
          Students
        </h1>
        <p className="mt-2 max-w-3xl text-[14px] leading-relaxed text-[#6b7280]">
          Admissions, enrollment, documents, and student status across your institution.
        </p>
      </header>

      <CollegeAdminPageTabs tabs={studentsTabs} className="mb-8" />

      {children}
    </div>
  );
}