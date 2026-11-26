"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchLibraryBookCataloguePage } from "@/features/college-admin/api/library-book-catalogue";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { LibraryBookCataloguePageQuery } from "@/features/college-admin/types/library-book-catalogue";

export function useLibraryBookCataloguePage(params?: LibraryBookCataloguePageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.libraryBookCataloguePage(params),
    queryFn: () => fetchLibraryBookCataloguePage(params),
  });
}