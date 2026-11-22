"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchPendingApprovalsOverview } from "@/features/college-admin/api/pending-approvals-overview";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { PendingApprovalsOverviewQuery } from "@/features/college-admin/types/pending-approvals-overview";

export function usePendingApprovalsOverview(params?: PendingApprovalsOverviewQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.pendingApprovalsOverview(params),
    queryFn: () => fetchPendingApprovalsOverview(params),
  });
}