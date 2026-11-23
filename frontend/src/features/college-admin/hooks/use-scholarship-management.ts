"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchScholarshipManagementPage } from "@/features/college-admin/api/finance-aid";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { ScholarshipManagementPageQuery } from "@/features/college-admin/types/scholarship-management";

export function useScholarshipManagementPage(params: ScholarshipManagementPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.scholarshipManagementPage(params),
    queryFn: () => fetchScholarshipManagementPage(params),
  });
}