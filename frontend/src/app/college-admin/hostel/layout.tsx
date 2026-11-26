import type { ReactNode } from "react";

import { HostelModuleChrome } from "@/features/college-admin/components/layout/hostel-module-chrome";

export default function HostelLayout({ children }: { children: ReactNode }) {
  return <HostelModuleChrome>{children}</HostelModuleChrome>;
}