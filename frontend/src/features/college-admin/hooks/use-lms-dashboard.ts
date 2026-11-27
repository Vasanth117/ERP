"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchLmsDashboardPage } from "@/features/college-admin/api/lms-dashboard";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useLmsDashboardPage(params?: { page?: number; page_size?: number }) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.lmsDashboardPage(params),
    queryFn: () => fetchLmsDashboardPage(params),
  });
}