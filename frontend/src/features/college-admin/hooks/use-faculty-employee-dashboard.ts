"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchFacultyEmployeeDashboardPage } from "@/features/college-admin/api/faculty";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { FacultyEmployeeDashboardQuery } from "@/features/college-admin/types/faculty-employee-dashboard";

export function useFacultyEmployeeDashboardPage(params?: FacultyEmployeeDashboardQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.facultyEmployeeDashboard(params),
    queryFn: () => fetchFacultyEmployeeDashboardPage(params),
  });
}