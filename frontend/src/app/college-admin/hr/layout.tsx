import type { ReactNode } from "react";

import { HrModuleChrome } from "@/features/college-admin/components/layout/hr-module-chrome";

export default function HrLayout({ children }: { children: ReactNode }) {
  return <HrModuleChrome>{children}</HrModuleChrome>;
}