"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchFacultyEmployeeHistoryPage } from "@/features/college-admin/api/faculty";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { FacultyEmployeeHistoryPageQuery } from "@/features/college-admin/types/faculty-employee-history";

export function useFacultyEmployeeHistoryPage(params: FacultyEmployeeHistoryPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.facultyEmployeeHistoryPage(params),
    queryFn: () => fetchFacultyEmployeeHistoryPage(params),
  });
}