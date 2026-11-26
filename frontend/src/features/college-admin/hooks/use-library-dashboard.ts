"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchLibraryDashboardPage } from "@/features/college-admin/api/library-dashboard";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { LibraryDashboardPageQuery } from "@/features/college-admin/types/library-dashboard";

export function useLibraryDashboardPage(params: LibraryDashboardPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.libraryDashboardPage(params),
    queryFn: () => fetchLibraryDashboardPage(params),
  });
}