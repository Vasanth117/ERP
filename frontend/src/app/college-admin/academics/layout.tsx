import type { ReactNode } from "react";

import { AcademicsModuleChrome } from "@/features/college-admin/components/layout/academics-module-chrome";

export default function AcademicsLayout({ children }: { children: ReactNode }) {
  return <AcademicsModuleChrome>{children}</AcademicsModuleChrome>;
}