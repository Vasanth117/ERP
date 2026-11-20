import type { ReactNode } from "react";

import { DashboardModuleChrome } from "@/features/college-admin/components/layout/dashboard-module-chrome";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return <DashboardModuleChrome>{children}</DashboardModuleChrome>;
}