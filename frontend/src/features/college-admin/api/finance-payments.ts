import { apiRequest } from "@/lib/api/client";

import type { OfflinePaymentCollectionPage, OfflinePaymentCollectionPageQuery } from "@/features/college-admin/types/offline-payment-collection";
import type { OnlinePaymentMonitoringPage, OnlinePaymentMonitoringPageQuery } from "@/features/college-admin/types/online-payment-monitoring";
import type { PaymentTransactionsPage, PaymentTransactionsPageQuery } from "@/features/college-admin/types/payment-transactions-page";

function toSearch(params: Record<string, string | number | undefined>) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchOnlinePaymentMonitoringPage(params?: OnlinePaymentMonitoringPageQuery) {
  return apiRequest<OnlinePaymentMonitoringPage>(
    `/college-admin/finance-administration/payments/online/page${toSearch(params ?? {})}`,
  );
}

export function fetchOfflinePaymentCollectionPage(params?: OfflinePaymentCollectionPageQuery) {
  return apiRequest<OfflinePaymentCollectionPage>(
    `/college-admin/finance-administration/payments/offline/page${toSearch(params ?? {})}`,
  );
}

export function fetchPaymentTransactionsPage(params?: PaymentTransactionsPageQuery) {
  return apiRequest<PaymentTransactionsPage>(
    `/college-admin/finance-administration/payments/transactions/page${toSearch(params ?? {})}`,
  );
}