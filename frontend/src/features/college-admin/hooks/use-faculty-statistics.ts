"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchFacultyStatisticsOverview } from "@/features/college-admin/api/faculty-statistics";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { FacultyStatisticsQuery } from "@/features/college-admin/types/faculty-statistics";

export function useFacultyStatisticsOverview(params?: FacultyStatisticsQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.facultyStatistics(params),
    queryFn: () => fetchFacultyStatisticsOverview(params),
  });
}