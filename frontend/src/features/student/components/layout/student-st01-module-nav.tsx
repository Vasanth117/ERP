"use client";

import { usePathname } from "next/navigation";

import { StudentPageTabs } from "@/features/student/components/layout/student-page-tabs";
import { isStudentSt01Path, studentSt01Tabs } from "@/features/student/config/st01-tabs";

/** ST 01 — horizontal module tabs only (no breadcrumb trail). */
export function StudentSt01ModuleNav() {
  const pathname = usePathname() ?? "";
  if (!isStudentSt01Path(pathname)) return null;

  return (
    <div className="mb-4" data-figma-node="164:227">
      <StudentPageTabs tabs={studentSt01Tabs} />
    </div>
  );
}