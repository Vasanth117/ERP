import { apiRequest } from "@/lib/api/client";

import type {
  RecentActivitiesOverview,
  RecentActivitiesOverviewQuery,
} from "@/features/college-admin/types/recent-activities-overview";

function buildQuery(params?: RecentActivitiesOverviewQuery): string {
  if (!params) return "";
  const q = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      q.set(key, String(value));
    }
  });
  const s = q.toString();
  return s ? `?${s}` : "";
}

export async function fetchRecentActivitiesOverview(
  params?: RecentActivitiesOverviewQuery,
): Promise<RecentActivitiesOverview> {
  return apiRequest<RecentActivitiesOverview>(
    `/college-admin/dashboard/recent-activities-overview${buildQuery(params)}`,
  );
}