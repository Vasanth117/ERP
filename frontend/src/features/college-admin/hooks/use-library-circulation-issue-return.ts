"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchLibraryCirculationIssueReturnPage } from "@/features/college-admin/api/library-circulation-issue-return";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { LibraryCirculationIssueReturnPageQuery } from "@/features/college-admin/types/library-circulation-issue-return";

export function useLibraryCirculationIssueReturnPage(params?: LibraryCirculationIssueReturnPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.libraryCirculationIssueReturnPage(params),
    queryFn: () => fetchLibraryCirculationIssueReturnPage(params),
  });
}