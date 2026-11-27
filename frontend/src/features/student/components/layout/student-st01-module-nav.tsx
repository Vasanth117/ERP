"use client";

import { usePathname } from "next/navigation";

import { StudentModuleChrome } from "@/features/student/components/layout/student-module-chrome";
import { isStudentSt01Path, studentSt01Tabs } from "@/features/student/config/st01-tabs";

/** ST 01 — module header then horizontal tabs. */
export function StudentSt01ModuleNav() {
  const pathname = usePathname() ?? "";
  if (!isStudentSt01Path(pathname)) return null;

  return (
    <StudentModuleChrome
      moduleKey="overview"
      tabs={studentSt01Tabs}
      figmaNode="164:227"
    />
  );
}