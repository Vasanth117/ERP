import type { ReactNode } from "react";

import { ReportsModuleChrome } from "@/features/college-admin/components/layout/reports-module-chrome";

export default function ReportsLayout({ children }: { children: ReactNode }) {
  return <ReportsModuleChrome>{children}</ReportsModuleChrome>;
}