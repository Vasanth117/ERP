"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchEmployeeDirectoryPage } from "@/features/college-admin/api/faculty";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { EmployeeDirectoryQuery } from "@/features/college-admin/types/employee-directory";

export function useEmployeeDirectoryPage(params?: EmployeeDirectoryQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.employeeDirectoryPage(params),
    queryFn: () => fetchEmployeeDirectoryPage(params),
  });
}