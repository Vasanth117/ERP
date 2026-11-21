"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchStudentAttendanceOverviewPage } from "@/features/college-admin/api/student-attendance-overview";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { StudentAttendanceOverviewQuery } from "@/features/college-admin/types/student-attendance-overview";

export function useStudentAttendanceOverviewPage(params?: StudentAttendanceOverviewQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.studentAttendanceOverview(params),
    queryFn: () => fetchStudentAttendanceOverviewPage(params),
  });
}