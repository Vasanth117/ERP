"use client";

import type { ReactNode } from "react";

import { FinanceCreationModal } from "@/features/college-admin/components/finance/finance-creation-modal";
import { CollegeAdminSectionChrome } from "@/features/college-admin/components/layout/college-admin-section-chrome";
import { financeTabs } from "@/features/college-admin/config/section-tabs";
import { FinanceCreationFlowProvider } from "@/features/college-admin/context/finance-creation-flow-context";

export function FinanceModuleChrome({ children }: { children: ReactNode }) {
  return (
    <FinanceCreationFlowProvider>
      <CollegeAdminSectionChrome
        moduleTitle="Finance"
        landingHref={financeTabs[0]!.href}
        tabs={financeTabs}
      >
        {children}
      </CollegeAdminSectionChrome>
      <FinanceCreationModal />
    </FinanceCreationFlowProvider>
  );
}