"use client";

import type { ReactNode } from "react";

import { CollegeAdminPageTabs } from "@/features/college-admin/components/layout/college-admin-page-tabs";
import { usersTabs } from "@/features/college-admin/config/section-tabs";

export function UsersModuleChrome({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto w-full max-w-[1440px]">
      <header className="mb-5">
        <h1 className="text-[26px] font-bold leading-tight tracking-[-0.02em] text-[#111827]">
          Users &amp; permissions
        </h1>
        <p className="mt-2 max-w-3xl text-[14px] leading-relaxed text-[#6b7280]">
          Manage institution accounts, roles, access rules, and account lifecycle.
        </p>
      </header>

      <CollegeAdminPageTabs tabs={usersTabs} className="mb-8" />

      {children}
    </div>
  );
}