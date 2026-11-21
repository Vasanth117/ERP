import type { ReactNode } from "react";

import { StudentsModuleChrome } from "@/features/college-admin/components/layout/students-module-chrome";

export default function StudentsLayout({ children }: { children: ReactNode }) {
  return <StudentsModuleChrome>{children}</StudentsModuleChrome>;
}