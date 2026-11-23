"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchPaymentTransactionsPage } from "@/features/college-admin/api/finance-payments";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { PaymentTransactionsPageQuery } from "@/features/college-admin/types/payment-transactions-page";

export function usePaymentTransactionsPage(params: PaymentTransactionsPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.paymentTransactionsPage(params),
    queryFn: () => fetchPaymentTransactionsPage(params),
  });
}