"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchOutstandingDuesManagementPage } from "@/features/college-admin/api/finance-receipts-dues";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { OutstandingDuesManagementPageQuery } from "@/features/college-admin/types/outstanding-dues-page";

export function useOutstandingDuesManagementPage(params: OutstandingDuesManagementPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.outstandingDuesManagementPage(params),
    queryFn: () => fetchOutstandingDuesManagementPage(params),
  });
}