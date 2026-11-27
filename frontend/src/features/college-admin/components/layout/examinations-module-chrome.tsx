"use client";

import type { ReactNode } from "react";

import { ExaminationCreationModal } from "@/features/college-admin/components/examinations/examination-creation-modal";
import { CollegeAdminSectionChrome } from "@/features/college-admin/components/layout/college-admin-section-chrome";
import { examinationsTabs } from "@/features/college-admin/config/section-tabs";
import { ExaminationCreationFlowProvider } from "@/features/college-admin/context/examination-creation-flow-context";

export function ExaminationsModuleChrome({ children }: { children: ReactNode }) {
  return (
    <ExaminationCreationFlowProvider>
      <CollegeAdminSectionChrome
        moduleTitle="Examinations"
        landingHref={examinationsTabs[0]!.href}
        tabs={examinationsTabs}
      >
        {children}
      </CollegeAdminSectionChrome>
      <ExaminationCreationModal />
    </ExaminationCreationFlowProvider>
  );
}