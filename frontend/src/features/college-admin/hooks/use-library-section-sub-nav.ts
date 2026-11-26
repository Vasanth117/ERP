"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchLibrarySectionSubNav } from "@/features/college-admin/api/library-section-sub-nav";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useLibrarySectionSubNav(path: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.librarySectionSubNav(path),
    queryFn: () => fetchLibrarySectionSubNav(path),
    enabled: Boolean(path),
  });
}