"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchHostelReportsPage } from "@/features/college-admin/api/hostel-reports";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { HostelReportsPageQuery } from "@/features/college-admin/types/hostel-reports";

export function useHostelReportsPage(params?: HostelReportsPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hostelReportsPage(params),
    queryFn: () => fetchHostelReportsPage(params),
  });
}