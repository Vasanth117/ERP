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
  /** When set, renders one line per entry (Figma-style wrapped copy under the module title). */
  moduleDescriptionLines?: readonly string[];
  /** First tab / home URL for this section. */
  landingHref: string;
  tabs: CollegeAdminTab[];
  tabsClassName?: string;
  children: ReactNode;
};

export function CollegeAdminSectionChrome({
  moduleTitle,
  moduleDescription,
  moduleDescriptionLines,
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
        <header
          className={cn(
            "mb-3",
            moduleDescription || moduleDescriptionLines?.length ? "mb-5" : undefined,
          )}
        >
          <h1 className="text-[26px] font-bold leading-tight tracking-[-0.02em] text-[#111827]">
            {moduleTitle}
          </h1>
          {moduleDescriptionLines?.length ? (
            <div className="mt-2 max-w-[44rem] text-[14px] leading-[1.45] text-[#6b7280]">
              {moduleDescriptionLines.map((line) => (
                <p key={line} className="block">
                  {line}
                </p>
              ))}
            </div>
          ) : moduleDescription ? (
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