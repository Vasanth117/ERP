"use client";

import { useMemo } from "react";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useCollegeAdminMutation as useMutation } from "@/features/college-admin/hooks/use-college-admin-mutation";
import {
  fetchCommunicationDeliveryStatusPage,
  fetchCommunicationHistoryPage,
  retryCommunicationFailedDeliveries,
} from "@/features/college-admin/api/communication-delivery-history";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useCommunicationDeliveryStatusPage(
  params?: { page?: number; page_size?: number },
  enabled = true,
) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.communicationDeliveryStatusPage(params),
    queryFn: () => fetchCommunicationDeliveryStatusPage(params),
    enabled,
  });
}

export function useCommunicationHistoryPage(
  params?: {
    page?: number;
    page_size?: number;
    search?: string;
    month?: string;
    channel?: string;
    sender?: string;
  },
  enabled = true,
) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.communicationHistoryPage(params),
    queryFn: () => fetchCommunicationHistoryPage(params),
    enabled,
  });
}

export function useRetryCommunicationFailedDeliveries() {
  return useMutation({ mutationFn: retryCommunicationFailedDeliveries });
}

export function useCommunicationDeliveryHistoryPage(
  variant: "delivery" | "history",
  params: Record<string, string | number | undefined>,
) {
  const deliveryParams = useMemo(() => ({ page: params.page as number, page_size: params.page_size as number }), [params.page, params.page_size]);
  const delivery = useCommunicationDeliveryStatusPage(deliveryParams, variant === "delivery");
  const history = useCommunicationHistoryPage(params, variant === "history");
  return variant === "history" ? history : delivery;
}