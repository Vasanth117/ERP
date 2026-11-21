"use client";

import { usePathname } from "next/navigation";

import { StudentPageTabs } from "@/features/student/components/layout/student-page-tabs";
import { isStudentSt02Path, studentSt02Tabs } from "@/features/student/config/st02-tabs";

/** ST 02 — horizontal module tabs matching Figma ST 02 (Overview, Semesters, Subjects & credits, Enrollment, Status). */
export function StudentSt02ModuleNav() {
  const pathname = usePathname() ?? "";
  if (!isStudentSt02Path(pathname)) return null;

  return (
    <div className="mb-5" data-figma-node="164:3627">
      <StudentPageTabs tabs={studentSt02Tabs} />
    </div>
  );
}
