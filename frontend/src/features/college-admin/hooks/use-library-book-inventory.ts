"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchLibraryBookInventoryPage } from "@/features/college-admin/api/library-book-inventory";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { LibraryBookInventoryPageQuery } from "@/features/college-admin/types/library-book-inventory";

export function useLibraryBookInventoryPage(params?: LibraryBookInventoryPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.libraryBookInventoryPage(params),
    queryFn: () => fetchLibraryBookInventoryPage(params),
  });
}