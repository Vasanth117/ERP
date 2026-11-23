"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchOnlinePaymentMonitoringPage } from "@/features/college-admin/api/finance-payments";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { OnlinePaymentMonitoringPageQuery } from "@/features/college-admin/types/online-payment-monitoring";

export function useOnlinePaymentMonitoringPage(params: OnlinePaymentMonitoringPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.onlinePaymentMonitoringPage(params),
    queryFn: () => fetchOnlinePaymentMonitoringPage(params),
  });
}