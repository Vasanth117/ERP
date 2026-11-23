"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchOfflinePaymentCollectionPage } from "@/features/college-admin/api/finance-payments";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { OfflinePaymentCollectionPageQuery } from "@/features/college-admin/types/offline-payment-collection";

export function useOfflinePaymentCollectionPage(params: OfflinePaymentCollectionPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.offlinePaymentCollectionPage(params),
    queryFn: () => fetchOfflinePaymentCollectionPage(params),
  });
}