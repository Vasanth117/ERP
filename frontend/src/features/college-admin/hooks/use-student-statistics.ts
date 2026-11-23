"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchStudentStatisticsOverview } from "@/features/college-admin/api/student-statistics";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { StudentStatisticsQuery } from "@/features/college-admin/types/student-statistics";

export function useStudentStatisticsOverview(params?: StudentStatisticsQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.studentStatistics(params),
    queryFn: () => fetchStudentStatisticsOverview(params),
  });
}