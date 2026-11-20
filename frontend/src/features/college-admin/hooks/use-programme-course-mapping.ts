"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchProgrammeCourseMappingPage } from "@/features/college-admin/api/organization";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useProgrammeCourseMappingPage(departmentId?: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.programmeCourseMappingPage(departmentId),
    queryFn: () => fetchProgrammeCourseMappingPage(departmentId),
  });
}