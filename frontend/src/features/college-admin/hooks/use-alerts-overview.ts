"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchAlertsOverview, markAllAlertsRead } from "@/features/college-admin/api/alerts-overview";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useAlertsOverview() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.alertsOverview(),
    queryFn: fetchAlertsOverview,
  });
}

export function useMarkAllAlertsRead() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: markAllAlertsRead,
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: collegeAdminQueryKeys.alertsOverview() });
    },
  });
}