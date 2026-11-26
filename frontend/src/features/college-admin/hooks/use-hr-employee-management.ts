"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchHrEmployeeManagementPage } from "@/features/college-admin/api/hr-employee-management";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { HrEmployeeManagementQuery } from "@/features/college-admin/types/hr-employee-management";

export function useHrEmployeeManagementPage(params?: HrEmployeeManagementQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hrEmployeeManagementPage(params),
    queryFn: () => fetchHrEmployeeManagementPage(params),
  });
}