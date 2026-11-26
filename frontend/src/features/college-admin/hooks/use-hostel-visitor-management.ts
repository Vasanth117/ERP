"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchHostelVisitorManagementPage } from "@/features/college-admin/api/hostel-visitor-management";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { HostelVisitorManagementPageQuery } from "@/features/college-admin/types/hostel-visitor-management";

export function useHostelVisitorManagementPage(params?: HostelVisitorManagementPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hostelVisitorManagementPage(params),
    queryFn: () => fetchHostelVisitorManagementPage(params),
  });
}