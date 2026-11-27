"use client";

import { usePathname } from "next/navigation";

import { StudentModuleChrome } from "@/features/student/components/layout/student-module-chrome";
import { isStudentSt04Path, studentSt04Tabs } from "@/features/student/config/st04-tabs";

/** ST 04 — module header then horizontal tabs. */
export function StudentSt04ModuleNav() {
  const pathname = usePathname() ?? "";
  if (!isStudentSt04Path(pathname)) return null;

  return (
    <StudentModuleChrome
      moduleKey="registration"
      tabs={studentSt04Tabs}
      figmaNode="164:10577"
    />
  );
}