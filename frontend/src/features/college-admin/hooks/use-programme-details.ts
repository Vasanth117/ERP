"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { fetchProgrammeDetailsPage } from "@/features/college-admin/api/academics";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useProgrammeDetailsPage(programmeId: string | null) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.programmeDetails(programmeId ?? ""),
    queryFn: () => fetchProgrammeDetailsPage(programmeId!),
    enabled: Boolean(programmeId),
  });
}