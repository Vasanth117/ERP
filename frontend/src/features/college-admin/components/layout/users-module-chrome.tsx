"use client";

import type { ReactNode } from "react";

import { CollegeAdminSectionChrome } from "@/features/college-admin/components/layout/college-admin-section-chrome";
import { usersTabs } from "@/features/college-admin/config/section-tabs";

export function UsersModuleChrome({ children }: { children: ReactNode }) {
  return (
    <CollegeAdminSectionChrome
      moduleTitle="Users & permissions"
      landingHref={usersTabs[0]!.href}
      tabs={usersTabs}
    >
      {children}
    </CollegeAdminSectionChrome>
  );
}