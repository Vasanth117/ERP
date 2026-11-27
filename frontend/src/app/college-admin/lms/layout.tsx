import type { ReactNode } from "react";

import { LmsModuleChrome } from "@/features/college-admin/components/layout/lms-module-chrome";

export default function LmsLayout({ children }: { children: ReactNode }) {
  return <LmsModuleChrome>{children}</LmsModuleChrome>;
}