"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchFinancialReportsPage } from "@/features/college-admin/api/finance-reconciliation-reports";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { FinancialReportsPageQuery } from "@/features/college-admin/types/financial-reports-page";

export function useFinancialReportsPage(params: FinancialReportsPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.financialReportsPage(params),
    queryFn: () => fetchFinancialReportsPage(params),
  });
}