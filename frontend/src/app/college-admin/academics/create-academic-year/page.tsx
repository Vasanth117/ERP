import { Suspense } from "react";

import { CreateAcademicYearDashboard } from "@/features/college-admin/components/academics/create-academic-year-dashboard";

export default function Page() {
  return (
    <Suspense
      fallback={
        <div className="rounded-xl border border-[#e8ecf2] bg-white p-6 text-sm text-[#6b7280]">Loading wizard…</div>
      }
    >
      <CreateAcademicYearDashboard />
    </Suspense>
  );
}