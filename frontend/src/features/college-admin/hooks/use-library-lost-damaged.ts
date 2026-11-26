"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchLibraryLostDamagedPage } from "@/features/college-admin/api/library-lost-damaged";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { LibraryLostDamagedPageQuery } from "@/features/college-admin/types/library-lost-damaged";

export function useLibraryLostDamagedPage(params?: LibraryLostDamagedPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.libraryLostDamagedPage(params),
    queryFn: () => fetchLibraryLostDamagedPage(params),
  });
}