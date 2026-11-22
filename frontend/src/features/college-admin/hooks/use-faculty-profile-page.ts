"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchFacultyProfilePage } from "@/features/college-admin/api/faculty";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useFacultyProfilePage(recordId: string | null) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.facultyProfilePage(recordId ?? ""),
    queryFn: () => fetchFacultyProfilePage(recordId!),
    enabled: Boolean(recordId),
  });
}