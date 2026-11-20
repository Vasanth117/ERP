"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchDepartmentPerformanceOverview } from "@/features/college-admin/api/department-performance";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { DepartmentPerformanceQuery } from "@/features/college-admin/types/department-performance";

export function useDepartmentPerformanceOverview(params?: DepartmentPerformanceQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.departmentPerformance(params),
    queryFn: () => fetchDepartmentPerformanceOverview(params),
  });
}