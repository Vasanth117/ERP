"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchHostelLeaveOutpassApprovalPage } from "@/features/college-admin/api/hostel-leave-outpass-approval";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { HostelLeaveOutpassApprovalPageQuery } from "@/features/college-admin/types/hostel-leave-outpass-approval";

export function useHostelLeaveOutpassApprovalPage(params?: HostelLeaveOutpassApprovalPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hostelLeaveOutpassApprovalPage(params),
    queryFn: () => fetchHostelLeaveOutpassApprovalPage(params),
  });
}