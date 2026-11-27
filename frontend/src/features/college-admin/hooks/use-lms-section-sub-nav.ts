"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchLmsSectionSubNav } from "@/features/college-admin/api/lms-section-sub-nav";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useLmsSectionSubNav(path: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.lmsSectionSubNav(path),
    queryFn: () => fetchLmsSectionSubNav(path),
    enabled: Boolean(path),
  });
}