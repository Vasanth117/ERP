"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchLibraryDigitalLibraryPage } from "@/features/college-admin/api/library-digital-library";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { LibraryDigitalLibraryPageQuery } from "@/features/college-admin/types/library-digital-library";

export function useLibraryDigitalLibraryPage(params?: LibraryDigitalLibraryPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.libraryDigitalLibraryPage(params),
    queryFn: () => fetchLibraryDigitalLibraryPage(params),
  });
}