import type { ReactNode } from "react";

import { FinanceModuleChrome } from "@/features/college-admin/components/layout/finance-module-chrome";

export default function FinanceLayout({ children }: { children: ReactNode }) {
  return <FinanceModuleChrome>{children}</FinanceModuleChrome>;
}