import type { ReactNode } from "react";

import { LibraryModuleChrome } from "@/features/college-admin/components/layout/library-module-chrome";

export default function LibraryLayout({ children }: { children: ReactNode }) {
  return <LibraryModuleChrome>{children}</LibraryModuleChrome>;
}