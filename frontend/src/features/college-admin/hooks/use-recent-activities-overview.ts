"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchRecentActivitiesOverview } from "@/features/college-admin/api/recent-activities-overview";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { RecentActivitiesOverviewQuery } from "@/features/college-admin/types/recent-activities-overview";

export function useRecentActivitiesOverview(params?: RecentActivitiesOverviewQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.recentActivitiesOverview(params),
    queryFn: () => fetchRecentActivitiesOverview(params),
  });
}