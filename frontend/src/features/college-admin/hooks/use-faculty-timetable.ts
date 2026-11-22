"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchFacultyTimetablePage } from "@/features/college-admin/api/faculty";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useFacultyTimetablePage(recordId?: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.facultyTimetablePage(recordId),
    queryFn: () => fetchFacultyTimetablePage(recordId),
  });
}