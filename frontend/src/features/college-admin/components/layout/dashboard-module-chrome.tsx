"use client";

import type { ReactNode } from "react";

import { CollegeAdminPageTabs } from "@/features/college-admin/components/layout/college-admin-page-tabs";
import { dashboardTabs } from "@/features/college-admin/config/section-tabs";

export function DashboardModuleChrome({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto w-full max-w-[1440px]">
      <header className="mb-3">
        <h1 className="text-[26px] font-bold leading-tight tracking-[-0.02em] text-[#111827]">
          College Admin Dashboard
        </h1>
      </header>

      <CollegeAdminPageTabs tabs={dashboardTabs} className="mb-4" />

      <h2 className="sr-only">Dashboard content</h2>
      {children}
    </div>
  );
}