"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchHrDashboardPage } from "@/features/college-admin/api/hr-dashboard";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { HrDashboardPageQuery } from "@/features/college-admin/types/hr-dashboard";

export function useHrDashboardPage(params: HrDashboardPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hrDashboardPage(params),
    queryFn: () => fetchHrDashboardPage(params),
  });
}