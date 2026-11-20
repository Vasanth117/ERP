import type { ReactNode } from "react";

import { OrganizationModuleChrome } from "@/features/college-admin/components/layout/organization-module-chrome";

export default function OrganizationLayout({ children }: { children: ReactNode }) {
  return <OrganizationModuleChrome>{children}</OrganizationModuleChrome>;
}