"use client";

import { useCollegeAdminDemoMode } from "@/features/college-admin/context/college-admin-demo-mode-context";

export function CollegeAdminDemoBanner() {
  const { demoMode, isHydrated } = useCollegeAdminDemoMode();
  if (!isHydrated || !demoMode) return null;

  return (
    <div
      className="mb-4 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-[#c7d7fe] bg-[#eef4ff] px-4 py-2.5 text-[13px] text-[#1e3a8a]"
      role="status"
    >
      <span>
        <span className="font-semibold">Demo mode is on.</span>{" "}
        You are viewing Grand Horizon Institute of Technology (GHIT) showcase data (read-only).
      </span>
      <span className="text-[12px] text-[#3b5cb8]">Turn off Demo mode in the sidebar to return to your college.</span>
    </div>
  );
}