import { Suspense } from "react";

import { StudentDetailsDashboard } from "@/features/college-admin/components/students/student-details-dashboard";

export default function Page() {
  return (
    <Suspense
      fallback={
        <div className="rounded-xl border border-[#e8ecf2] bg-white p-6 text-sm text-[#6b7280]">Loading student…</div>
      }
    >
      <StudentDetailsDashboard />
    </Suspense>
  );
}