"use client";

import { useQuery } from "@tanstack/react-query";

import {
  fetchDashboardOverview,
  fetchDashboardStatistics,
  fetchOperationalSummaries,
  fetchPendingApprovals,
  fetchRecentActivities,
  type DashboardQuery,
} from "@/features/college-admin/api/dashboard";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useDashboardOverview(params: DashboardQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.dashboard(params as Record<string, string>),
    queryFn: () => fetchDashboardOverview(params),
  });
}

export function useDashboardStatistics(params?: {
  department_id?: string;
  academic_year_label?: string;
}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.dashboardStats(params),
    queryFn: () => fetchDashboardStatistics(params),
  });
}

export function useOperationalSummaries(academicYear?: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.dashboardOperations({
      academic_year_label: academicYear,
    }),
    queryFn: () =>
      fetchOperationalSummaries(
        academicYear ? { academic_year_label: academicYear } : {},
      ),
  });
}

export function usePendingApprovals(offset = 0, limit = 20) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.pendingApprovals(offset, limit),
    queryFn: () => fetchPendingApprovals(offset, limit),
  });
}

export function useRecentActivities(
  offset = 0,
  limit = 20,
  range?: DashboardQuery["range"],
) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.activities(offset, limit, range),
    queryFn: () => fetchRecentActivities(offset, limit, range ?? "week"),
  });
}