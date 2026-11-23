"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchFeeDemandInvoiceManagementPage } from "@/features/college-admin/api/fee-demand-invoice-management";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { FeeDemandInvoiceManagementPageQuery } from "@/features/college-admin/types/fee-demand-invoice-management";

export function useFeeDemandInvoiceManagementPage(params: FeeDemandInvoiceManagementPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.feeDemandInvoiceManagementPage(params),
    queryFn: () => fetchFeeDemandInvoiceManagementPage(params),
  });
}