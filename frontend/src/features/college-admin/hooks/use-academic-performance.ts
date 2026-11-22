"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchAcademicPerformanceOverview } from "@/features/college-admin/api/academic-performance";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { AcademicPerformanceQuery } from "@/features/college-admin/types/academic-performance";

export function useAcademicPerformanceOverview(params?: AcademicPerformanceQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.academicPerformance(params),
    queryFn: () => fetchAcademicPerformanceOverview(params),
  });
}