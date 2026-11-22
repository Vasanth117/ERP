"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchProgrammeCourseMappingPage } from "@/features/college-admin/api/organization";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useProgrammeCourseMappingPage(departmentId?: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.programmeCourseMappingPage(departmentId),
    queryFn: () => fetchProgrammeCourseMappingPage(departmentId),
  });
}