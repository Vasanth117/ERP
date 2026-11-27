"use client";

import { usePathname } from "next/navigation";

import { StudentModuleChrome } from "@/features/student/components/layout/student-module-chrome";
import { isStudentSt02Path, studentSt02Tabs } from "@/features/student/config/st02-tabs";

/** ST 02 — module header then horizontal tabs (Overview … Programme & Department). */
export function StudentSt02ModuleNav() {
  const pathname = usePathname() ?? "";
  if (!isStudentSt02Path(pathname)) return null;

  return (
    <StudentModuleChrome
      moduleKey="academics"
      tabs={studentSt02Tabs}
      figmaNode="164:3627"
    />
  );
}
