"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchAttendanceDashboardPage } from "@/features/college-admin/api/attendance-dashboard";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { AttendanceDashboardQuery } from "@/features/college-admin/types/attendance-dashboard";

export function useAttendanceDashboardPage(params?: AttendanceDashboardQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.attendanceDashboard(params),
    queryFn: () => fetchAttendanceDashboardPage(params),
  });
}