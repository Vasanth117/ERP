import type { ReactNode } from "react";

import { InstitutionModuleChrome } from "@/features/college-admin/components/layout/institution-module-chrome";

export default function InstitutionLayout({ children }: { children: ReactNode }) {
  return <InstitutionModuleChrome>{children}</InstitutionModuleChrome>;
}