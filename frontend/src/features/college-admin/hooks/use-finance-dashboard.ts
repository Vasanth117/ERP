"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchFinanceDashboardPage } from "@/features/college-admin/api/finance-dashboard";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { FinanceDashboardPageQuery } from "@/features/college-admin/types/finance-dashboard";

export function useFinanceDashboardPage(params: FinanceDashboardPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.financeDashboardPage(params),
    queryFn: () => fetchFinanceDashboardPage(params),
  });
}