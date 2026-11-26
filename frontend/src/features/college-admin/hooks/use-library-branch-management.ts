"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchLibraryBranchManagementPage } from "@/features/college-admin/api/library-branch-management";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useLibraryBranchManagementPage() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.libraryBranchManagementPage(),
    queryFn: () => fetchLibraryBranchManagementPage(),
  });
}