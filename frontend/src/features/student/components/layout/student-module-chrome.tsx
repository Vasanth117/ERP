"use client";

import { StudentPageTabs } from "@/features/student/components/layout/student-page-tabs";
import { PORTAL_MODULE_TITLE } from "@/features/student/components/ui/student-portal-tokens";
import type { CollegeAdminTab } from "@/features/college-admin/config/section-tabs";
import {
  studentModuleChrome,
  type StudentModuleKey,
} from "@/features/student/config/section-tabs";

type StudentModuleChromeProps = {
  moduleKey: StudentModuleKey;
  tabs: CollegeAdminTab[];
  figmaNode?: string;
};

/** Module title → horizontal tabs (spacing matches college admin dashboard chrome). */
export function StudentModuleChrome({ moduleKey, tabs, figmaNode }: StudentModuleChromeProps) {
  const def = studentModuleChrome[moduleKey];

  return (
    <div data-figma-node={figmaNode}>
      <header className="mb-3">
        <h1 className={PORTAL_MODULE_TITLE}>{def.title}</h1>
      </header>
      <StudentPageTabs tabs={tabs} className="mb-4" />
    </div>
  );
}