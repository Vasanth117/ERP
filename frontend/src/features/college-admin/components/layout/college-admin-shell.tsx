import type { ReactNode } from "react";

import { CollegeAdminHeader } from "@/features/college-admin/components/layout/college-admin-header";
import { CollegeAdminSectionNav } from "@/features/college-admin/components/layout/college-admin-section-nav";
import { CollegeAdminSidebar } from "@/features/college-admin/components/layout/college-admin-sidebar";

export function CollegeAdminShell({ children }: { children: ReactNode }) {
  return (
    <div
      className="flex min-h-screen bg-[#f5f8ff]"
      style={{
        backgroundImage:
          "linear-gradient(151.93deg, rgb(245, 248, 255) 14.286%, rgb(237, 242, 251) 85.714%)",
      }}
    >
      <CollegeAdminSidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <CollegeAdminHeader />
        <CollegeAdminSectionNav />
        <main className="flex-1 overflow-auto p-6 md:p-8">{children}</main>
      </div>
    </div>
  );
}