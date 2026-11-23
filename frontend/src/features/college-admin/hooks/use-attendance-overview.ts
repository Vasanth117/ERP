"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchAttendanceOverview } from "@/features/college-admin/api/attendance-overview";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { AttendanceOverviewQuery } from "@/features/college-admin/types/attendance-overview";

export function useAttendanceOverview(params?: AttendanceOverviewQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.attendanceOverview(params),
    queryFn: () => fetchAttendanceOverview(params),
  });
}