import { apiRequest } from "@/lib/api/client";

import type { FinanceOverview, FinanceOverviewQuery } from "@/features/college-admin/types/finance-overview";

function buildQuery(params?: FinanceOverviewQuery): string {
  if (!params) return "";
  const q = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      q.set(key, value);
    }
  });
  const s = q.toString();
  return s ? `?${s}` : "";
}

export async function fetchFinanceOverview(params?: FinanceOverviewQuery): Promise<FinanceOverview> {
  return apiRequest<FinanceOverview>(`/college-admin/dashboard/finance-summary${buildQuery(params)}`);
}