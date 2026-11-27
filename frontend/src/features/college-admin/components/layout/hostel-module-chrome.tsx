"use client";

import type { ReactNode } from "react";

import { CollegeAdminSectionChrome } from "@/features/college-admin/components/layout/college-admin-section-chrome";
import type { CollegeAdminTab } from "@/features/college-admin/config/section-tabs";
import { hostelSectionTabs } from "@/features/college-admin/config/hostel-section-tabs";

const hostelModuleTabs = hostelSectionTabs as CollegeAdminTab[];
const HOSTEL_LANDING_HREF =
  hostelModuleTabs[0]?.href ?? "/college-admin/hostel/hostel-dashboard";

export function HostelModuleChrome({ children }: { children: ReactNode }) {
  return (
    <CollegeAdminSectionChrome
      moduleTitle="Hostel"
      landingHref={HOSTEL_LANDING_HREF}
      tabs={hostelModuleTabs}
    >
      {children}
    </CollegeAdminSectionChrome>
  );
}