"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchRoleManagementDashboardPage } from "@/features/college-admin/api/users";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useRoleManagementDashboardPage(page = 1) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.roleManagementDashboard(page),
    queryFn: () => fetchRoleManagementDashboardPage(page),
  });
}