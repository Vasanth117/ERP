"use client";

import type { ReactNode } from "react";

import { CollegeAdminDemoModeProvider } from "@/features/college-admin/context/college-admin-demo-mode-context";

/** Client boundary so demo mode context wraps the full college-admin tree. */
export function CollegeAdminProviders({ children }: { children: ReactNode }) {
  return <CollegeAdminDemoModeProvider>{children}</CollegeAdminDemoModeProvider>;
}