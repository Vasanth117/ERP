import { apiRequest } from "@/lib/api/client";

import type {
  PendingApprovalsOverview,
  PendingApprovalsOverviewQuery,
} from "@/features/college-admin/types/pending-approvals-overview";

function buildQuery(params?: PendingApprovalsOverviewQuery): string {
  if (!params) return "";
  const q = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      q.set(key === "range" ? "range" : key, value);
    }
  });
  const s = q.toString();
  return s ? `?${s}` : "";
}

export async function fetchPendingApprovalsOverview(
  params?: PendingApprovalsOverviewQuery,
): Promise<PendingApprovalsOverview> {
  return apiRequest<PendingApprovalsOverview>(
    `/college-admin/dashboard/pending-approvals-overview${buildQuery(params)}`,
  );
}