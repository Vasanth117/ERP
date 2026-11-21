import type { ReactNode } from "react";

import { FacultyModuleChrome } from "@/features/college-admin/components/layout/faculty-module-chrome";

export default function FacultyLayout({ children }: { children: ReactNode }) {
  return <FacultyModuleChrome>{children}</FacultyModuleChrome>;
}