"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchHostelDashboardPage } from "@/features/college-admin/api/hostel-dashboard";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { HostelDashboardPageQuery } from "@/features/college-admin/types/hostel-dashboard";

export function useHostelDashboardPage(params?: HostelDashboardPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hostelDashboardPage(params),
    queryFn: () => fetchHostelDashboardPage(params),
  });
}