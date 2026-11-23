"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchPaymentReconciliationPage } from "@/features/college-admin/api/finance-reconciliation-reports";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { PaymentReconciliationPageQuery } from "@/features/college-admin/types/payment-reconciliation";

export function usePaymentReconciliationPage(params: PaymentReconciliationPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.paymentReconciliationPage(params),
    queryFn: () => fetchPaymentReconciliationPage(params),
  });
}