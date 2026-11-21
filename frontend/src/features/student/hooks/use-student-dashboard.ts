"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchBacklogSummary } from "@/features/student/api/arrears";
import {
  fetchDashboardActivities,
  fetchStudentDashboard,
  fetchStudentDashboardStats,
} from "@/features/student/api/dashboard";
import { fetchCgpa } from "@/features/student/api/grading";
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

export function useStudentCgpa() {
  return useQuery({
    queryKey: studentQueryKeys.dashboardCgpa(),
    queryFn: fetchCgpa,
    retry: false,
  });
}

export function useStudentBacklogSummary() {
  return useQuery({
    queryKey: studentQueryKeys.dashboardBacklog(),
    queryFn: fetchBacklogSummary,
    retry: false,
  });
}