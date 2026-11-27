"use client";

import type { ReactNode } from "react";

import { CollegeAdminSectionChrome } from "@/features/college-admin/components/layout/college-admin-section-chrome";
import type { CollegeAdminTab } from "@/features/college-admin/config/section-tabs";
import { communicationSectionTabs } from "@/features/college-admin/config/communication-section-tabs";

const communicationModuleTabs = communicationSectionTabs as CollegeAdminTab[];
const COMMUNICATION_LANDING_HREF =
  communicationModuleTabs[0]?.href ?? "/college-admin/communication/communication-dashboard";

export function CommunicationModuleChrome({ children }: { children: ReactNode }) {
  return (
    <CollegeAdminSectionChrome
      moduleTitle="Communication"
      landingHref={COMMUNICATION_LANDING_HREF}
      tabs={communicationModuleTabs}
    >
      {children}
    </CollegeAdminSectionChrome>
  );
}