"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchHostelFeeManagementPage } from "@/features/college-admin/api/hostel-fee-management";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { HostelFeeManagementPageQuery } from "@/features/college-admin/types/hostel-fee-management";

export function useHostelFeeManagementPage(params?: HostelFeeManagementPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hostelFeeManagementPage(params),
    queryFn: () => fetchHostelFeeManagementPage(params),
  });
}