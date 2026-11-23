"use client";

import type { ReactNode } from "react";
import { usePathname } from "next/navigation";

import { CollegeAdminPageTabs } from "@/features/college-admin/components/layout/college-admin-page-tabs";
import type { CollegeAdminTab } from "@/features/college-admin/config/section-tabs";
import { cn } from "@/lib/utils";

export type CollegeAdminSectionChromeProps = {
  /** Shown only on the section landing route (e.g. “College Admin Dashboard”). */
  moduleTitle: string;
  moduleDescription?: string;
  /** First tab / home URL for this section. */
  landingHref: string;
  tabs: CollegeAdminTab[];
  tabsClassName?: string;
  children: ReactNode;
};

export function CollegeAdminSectionChrome({
  moduleTitle,
  moduleDescription,
  landingHref,
  tabs,
  tabsClassName,
  children,
}: CollegeAdminSectionChromeProps) {
  const pathname = usePathname() ?? "";
  const isLanding = pathname === landingHref;

  return (
    <div className="mx-auto w-full max-w-[1440px]">
      {isLanding ? (
        <header className={cn("mb-3", moduleDescription ? "mb-5" : undefined)}>
          <h1 className="text-[26px] font-bold leading-tight tracking-[-0.02em] text-[#111827]">
            {moduleTitle}
          </h1>
          {moduleDescription ? (
            <p className="mt-2 max-w-3xl text-[14px] leading-relaxed text-[#6b7280]">
              {moduleDescription}
            </p>
          ) : null}
        </header>
      ) : null}

      <CollegeAdminPageTabs tabs={tabs} className={cn(isLanding ? "mb-4" : "mb-8", tabsClassName)} />

      {children}
    </div>
  );
}