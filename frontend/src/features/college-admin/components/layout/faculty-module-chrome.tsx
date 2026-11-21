"use client";

import type { ReactNode } from "react";

import { CollegeAdminPageTabs } from "@/features/college-admin/components/layout/college-admin-page-tabs";
import { facultyTabs } from "@/features/college-admin/config/section-tabs";

export function FacultyModuleChrome({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto w-full max-w-[1440px]">
      <header className="mb-5">
        <h1 className="text-[26px] font-bold leading-tight tracking-[-0.02em] text-[#111827]">
          Faculty & Employees
        </h1>
        <p className="mt-2 max-w-3xl text-[14px] leading-relaxed text-[#6b7280]">
          Faculty and staff directories, assignments, workload, documents, and employment status for your institution.
        </p>
      </header>

      <CollegeAdminPageTabs tabs={facultyTabs} className="mb-8" />

      {children}
    </div>
  );
}