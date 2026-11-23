"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchRefundManagementPage } from "@/features/college-admin/api/finance-aid";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { RefundManagementPageQuery } from "@/features/college-admin/types/refund-management-page";

export function useRefundManagementPage(params: RefundManagementPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.refundManagementPage(params),
    queryFn: () => fetchRefundManagementPage(params),
  });
}