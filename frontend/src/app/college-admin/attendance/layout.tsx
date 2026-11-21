import type { ReactNode } from "react";

import { AttendanceModuleChrome } from "@/features/college-admin/components/layout/attendance-module-chrome";

export default function AttendanceLayout({ children }: { children: ReactNode }) {
  return <AttendanceModuleChrome>{children}</AttendanceModuleChrome>;
}