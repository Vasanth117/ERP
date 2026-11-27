"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchCommunicationDashboardPage } from "@/features/college-admin/api/communication-dashboard";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { CommunicationDashboardPageQuery } from "@/features/college-admin/types/communication-dashboard";

export function useCommunicationDashboardPage(params?: CommunicationDashboardPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.communicationDashboardPage(params),
    queryFn: () => fetchCommunicationDashboardPage(params),
  });
}