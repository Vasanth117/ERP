import { Suspense } from "react";

import { ProgrammeDetailsDashboard } from "@/features/college-admin/components/academics/programme-details-dashboard";

export default function Page() {
  return (
    <Suspense
      fallback={
        <div className="rounded-2xl border border-[#e5e7eb] bg-white p-6 text-sm text-[#64748b]">Loading programme…</div>
      }
    >
      <ProgrammeDetailsDashboard />
    </Suspense>
  );
}