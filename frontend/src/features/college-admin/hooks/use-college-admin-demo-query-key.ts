"use client";

import { useMemo } from "react";

import { useCollegeAdminDemoMode } from "@/features/college-admin/context/college-admin-demo-mode-context";

/** Suffix so live vs showcase demo data never share the same React Query cache. */
export function useCollegeAdminDemoQueryKey<T extends readonly unknown[]>(
  base: T,
): readonly [...T, "demo-showcase" | "live"] {
  const { demoMode } = useCollegeAdminDemoMode();
  return useMemo(
    () => [...base, demoMode ? "demo-showcase" : "live"] as const,
    [base, demoMode],
  );
}