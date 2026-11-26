"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchLibraryReportsPage } from "@/features/college-admin/api/library-reports";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { LibraryReportsPageQuery } from "@/features/college-admin/types/library-reports";

export function useLibraryReportsPage(params?: LibraryReportsPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.libraryReportsPage(params),
    queryFn: () => fetchLibraryReportsPage(params),
  });
}