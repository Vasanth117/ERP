"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchDepartmentResourceManagementPage } from "@/features/college-admin/api/organization";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useDepartmentResourceManagementPage(departmentId?: string, view?: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.departmentResourceManagementPage(
      departmentId ? `${departmentId}:${view ?? ""}` : view,
    ),
    queryFn: () => fetchDepartmentResourceManagementPage(departmentId, view),
  });
}