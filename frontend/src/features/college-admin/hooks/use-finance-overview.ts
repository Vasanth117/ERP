"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchFinanceOverview } from "@/features/college-admin/api/finance-overview";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { FinanceOverviewQuery } from "@/features/college-admin/types/finance-overview";

export function useFinanceOverview(params?: FinanceOverviewQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.financeOverview(params),
    queryFn: () => fetchFinanceOverview(params),
  });
}