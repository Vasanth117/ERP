"use client";

import { usePathname } from "next/navigation";

import { StudentModuleChrome } from "@/features/student/components/layout/student-module-chrome";
import { isStudentSt03Path, studentSt03Tabs } from "@/features/student/config/st03-tabs";

/** ST 03 — module header then horizontal tabs. */
export function StudentSt03ModuleNav() {
  const pathname = usePathname() ?? "";
  if (!isStudentSt03Path(pathname)) return null;

  return (
    <StudentModuleChrome
      moduleKey="curriculum"
      tabs={studentSt03Tabs}
      figmaNode="164:7289"
    />
  );
}