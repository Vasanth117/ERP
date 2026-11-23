"use client";

import { fetchAcademicYearDetailsPage } from "@/features/college-admin/api/academics";
import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useAcademicYearDetailsPage(yearId: string | null) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.academicYearDetails(yearId ?? ""),
    queryFn: () => fetchAcademicYearDetailsPage(yearId!),
    enabled: Boolean(yearId),
  });
}