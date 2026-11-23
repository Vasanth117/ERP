import { apiRequest } from "@/lib/api/client";

import type { FinancialReportsPage, FinancialReportsPageQuery } from "@/features/college-admin/types/financial-reports-page";
import type { PaymentReconciliationPage, PaymentReconciliationPageQuery } from "@/features/college-admin/types/payment-reconciliation";

function toSearch(params: Record<string, string | number | undefined>) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchPaymentReconciliationPage(params?: PaymentReconciliationPageQuery) {
  return apiRequest<PaymentReconciliationPage>(
    `/college-admin/finance-administration/reconciliation/page${toSearch(params ?? {})}`,
  );
}

export function fetchFinancialReportsPage(params?: FinancialReportsPageQuery) {
  return apiRequest<FinancialReportsPage>(
    `/college-admin/finance-administration/reports/financial/page${toSearch(params ?? {})}`,
  );
}