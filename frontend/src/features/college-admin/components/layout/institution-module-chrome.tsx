"use client";

import type { ReactNode } from "react";

import { CollegeAdminPageTabs } from "@/features/college-admin/components/layout/college-admin-page-tabs";
import { institutionTabs } from "@/features/college-admin/config/section-tabs";

export function InstitutionModuleChrome({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto w-full max-w-[1440px]">
      <header className="mb-5">
        <h1 className="text-[26px] font-bold leading-tight tracking-[-0.02em] text-[#111827]">
          Institution &amp; campus
        </h1>
        <p className="mt-2 max-w-3xl text-[14px] leading-relaxed text-[#6b7280]">
          Profile, branding, policies, and campus configuration for your college.
        </p>
      </header>

      <CollegeAdminPageTabs tabs={institutionTabs} className="mb-8" />

      {children}
    </div>
  );
}