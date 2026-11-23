"use client";

import type { ReactNode } from "react";

import { CollegeAdminDemoBanner } from "@/features/college-admin/components/layout/college-admin-demo-banner";
import { CollegeAdminSidebar } from "@/features/college-admin/components/layout/college-admin-sidebar";

export function CollegeAdminShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen bg-white">
      <CollegeAdminSidebar />
      <div className="flex min-w-0 flex-1 flex-col bg-white">
        <main className="flex-1 overflow-auto bg-white px-6 py-5 md:px-8 md:py-6">
          <CollegeAdminDemoBanner />
          {children}
        </main>
      </div>
    </div>
  );
}