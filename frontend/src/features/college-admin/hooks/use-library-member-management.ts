"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchLibraryMemberManagementPage } from "@/features/college-admin/api/library-member-management";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { LibraryMemberManagementPageQuery } from "@/features/college-admin/types/library-member-management";

export function useLibraryMemberManagementPage(params?: LibraryMemberManagementPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.libraryMemberManagementPage(params),
    queryFn: () => fetchLibraryMemberManagementPage(params),
  });
}