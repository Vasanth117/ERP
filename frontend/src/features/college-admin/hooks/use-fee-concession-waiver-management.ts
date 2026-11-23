"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchConcessionWaiverManagementPage } from "@/features/college-admin/api/finance-aid";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { ConcessionWaiverManagementPageQuery } from "@/features/college-admin/types/fee-concession-waiver-management";

export function useConcessionWaiverManagementPage(params: ConcessionWaiverManagementPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.feeConcessionWaiverManagementPage(params),
    queryFn: () => fetchConcessionWaiverManagementPage(params),
  });
}