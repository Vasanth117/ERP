"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchReceiptManagementPage } from "@/features/college-admin/api/finance-receipts-dues";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { ReceiptManagementPageQuery } from "@/features/college-admin/types/receipt-management";

export function useReceiptManagementPage(params: ReceiptManagementPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.receiptManagementPage(params),
    queryFn: () => fetchReceiptManagementPage(params),
  });
}