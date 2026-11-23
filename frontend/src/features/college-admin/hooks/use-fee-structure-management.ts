"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchFeeStructureManagementPage } from "@/features/college-admin/api/fee-structure-management";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { FeeStructureManagementPageQuery } from "@/features/college-admin/types/fee-structure-management";

export function useFeeStructureManagementPage(params: FeeStructureManagementPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.feeStructureManagementPage(params),
    queryFn: () => fetchFeeStructureManagementPage(params),
  });
}