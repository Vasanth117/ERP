import type { ReactNode } from "react";

import { ExaminationsModuleChrome } from "@/features/college-admin/components/layout/examinations-module-chrome";

export default function ExaminationsLayout({ children }: { children: ReactNode }) {
  return <ExaminationsModuleChrome>{children}</ExaminationsModuleChrome>;
}