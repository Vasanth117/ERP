import type { ReactNode } from "react";

import { CollegeAdminShell } from "@/features/college-admin/components/layout/college-admin-shell";

export default function CollegeAdminLayout({ children }: { children: ReactNode }) {
  return <CollegeAdminShell>{children}</CollegeAdminShell>;
}