"use client";

import type { ReactNode } from "react";

import { CollegeAdminSectionChrome } from "@/features/college-admin/components/layout/college-admin-section-chrome";
import type { CollegeAdminTab } from "@/features/college-admin/config/section-tabs";
import { librarySectionTabs } from "@/features/college-admin/config/library-section-tabs";

const libraryModuleTabs = librarySectionTabs as CollegeAdminTab[];
const LIBRARY_LANDING_HREF =
  libraryModuleTabs[0]?.href ?? "/college-admin/library/library-dashboard";

export function LibraryModuleChrome({ children }: { children: ReactNode }) {
  return (
    <CollegeAdminSectionChrome
      moduleTitle="Library"
      landingHref={LIBRARY_LANDING_HREF}
      tabs={libraryModuleTabs}
    >
      {children}
    </CollegeAdminSectionChrome>
  );
}