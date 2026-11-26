"use client";

import type { ReactNode } from "react";

import { CollegeAdminSectionChrome } from "@/features/college-admin/components/layout/college-admin-section-chrome";
import { HostelSectionSubNavBar } from "@/features/college-admin/components/hostel/hostel-section-sub-nav-bar";
import type { CollegeAdminTab } from "@/features/college-admin/config/section-tabs";
import { hostelSectionTabs } from "@/features/college-admin/config/hostel-section-tabs";

const hostelModuleTabs = hostelSectionTabs as CollegeAdminTab[];
const HOSTEL_LANDING_HREF =
  hostelModuleTabs[0]?.href ?? "/college-admin/hostel/hostel-dashboard";

export function HostelModuleChrome({ children }: { children: ReactNode }) {
  return (
    <CollegeAdminSectionChrome
      moduleTitle="Hostel"
      moduleDescriptionLines={[
        "Buildings and rooms, admissions and bed allocation, residents,",
        "fees and mess, visitors and outpass, maintenance, incidents, and reporting.",
      ]}
      landingHref={HOSTEL_LANDING_HREF}
      tabs={hostelModuleTabs}
    >
      <HostelSectionSubNavBar />
      {children}
    </CollegeAdminSectionChrome>
  );
}