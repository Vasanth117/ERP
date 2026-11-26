"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { EmployeeProfileManagementDashboard } from "@/features/college-admin/components/faculty/employee-profile-management-dashboard";

export function HrEmployeeDetailScreen() {
  const searchParams = useSearchParams();
  const recordId = searchParams.get("record_id") ?? searchParams.get("id");

  return (
    <div className="space-y-4">
      <Link
        href="/college-admin/hr/employee-management"
        className="inline-flex items-center gap-1.5 text-[13px] font-medium text-[#245dd8] hover:underline"
      >
        <ChevronLeftIcon className="size-4" aria-hidden />
        Back to Employee Management
      </Link>
      {recordId ? (
        <EmployeeProfileManagementDashboard />
      ) : (
        <p className="rounded-xl border border-dashed border-[#dce3ec] bg-[#f8fafc] p-8 text-center text-sm text-[#6b7280]">
          Select an employee from the{" "}
          <Link href="/college-admin/hr/employee-management" className="text-[#245dd8] hover:underline">
            employee directory
          </Link>{" "}
          to view full details.
        </p>
      )}
    </div>
  );
}