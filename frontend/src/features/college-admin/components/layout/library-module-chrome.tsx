"use client";

import type { ReactNode } from "react";

import { CollegeAdminSectionChrome } from "@/features/college-admin/components/layout/college-admin-section-chrome";
import { LibrarySectionSubNavBar } from "@/features/college-admin/components/library/library-section-sub-nav-bar";
import type { CollegeAdminTab } from "@/features/college-admin/config/section-tabs";
import { librarySectionTabs } from "@/features/college-admin/config/library-section-tabs";

const libraryModuleTabs = librarySectionTabs as CollegeAdminTab[];
const LIBRARY_LANDING_HREF =
  libraryModuleTabs[0]?.href ?? "/college-admin/library/library-dashboard";

export function LibraryModuleChrome({ children }: { children: ReactNode }) {
  return (
    <CollegeAdminSectionChrome
      moduleTitle="Library"
      moduleDescription="Catalogue, inventory, circulation, and member services across library branches. Digital resources, fines, reports, and library configuration."
      landingHref={LIBRARY_LANDING_HREF}
      tabs={libraryModuleTabs}
    >
      <LibrarySectionSubNavBar />
      {children}
    </CollegeAdminSectionChrome>
  );
}