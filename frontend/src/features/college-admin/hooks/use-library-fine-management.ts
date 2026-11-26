"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchLibraryFineManagementPage } from "@/features/college-admin/api/library-fine-management";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { LibraryFineManagementPageQuery } from "@/features/college-admin/types/library-fine-management";

export function useLibraryFineManagementPage(params?: LibraryFineManagementPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.libraryFineManagementPage(params),
    queryFn: () => fetchLibraryFineManagementPage(params),
  });
}