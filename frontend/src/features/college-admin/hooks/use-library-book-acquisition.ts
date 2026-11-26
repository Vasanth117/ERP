"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchLibraryBookAcquisitionPage } from "@/features/college-admin/api/library-book-acquisition";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { LibraryBookAcquisitionPageQuery } from "@/features/college-admin/types/library-book-acquisition";

export function useLibraryBookAcquisitionPage(params?: LibraryBookAcquisitionPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.libraryBookAcquisitionPage(params),
    queryFn: () => fetchLibraryBookAcquisitionPage(params),
  });
}