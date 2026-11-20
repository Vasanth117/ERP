"use client";

import { useQuery } from "@tanstack/react-query";

import {
  fetchDashboardActivities,
  fetchStudentDashboard,
  fetchStudentDashboardStats,
} from "@/features/student/api/dashboard";
import { studentQueryKeys } from "@/features/student/query-keys";

export function useStudentDashboard(range = "week") {
  return useQuery({
    queryKey: studentQueryKeys.dashboard(range),
    queryFn: () => fetchStudentDashboard(range),
  });
}

export function useStudentDashboardStats() {
  return useQuery({
    queryKey: studentQueryKeys.dashboardStats(),
    queryFn: fetchStudentDashboardStats,
  });
}

export function useDashboardActivities(limit = 20, offset = 0) {
  return useQuery({
    queryKey: studentQueryKeys.dashboardActivities(limit, offset),
    queryFn: () => fetchDashboardActivities(limit, offset),
  });
}