"use client";

import { usePathname } from "next/navigation";

import { StudentModuleChrome } from "@/features/student/components/layout/student-module-chrome";
import { isStudentSt05Path, studentSt05Tabs } from "@/features/student/config/st05-tabs";

/** ST 05 — module header then horizontal tabs. */
export function StudentSt05ModuleNav() {
  const pathname = usePathname() ?? "";
  if (!isStudentSt05Path(pathname)) return null;

  return (
    <StudentModuleChrome
      moduleKey="timetable"
      tabs={studentSt05Tabs}
      figmaNode="164:14233"
    />
  );
}