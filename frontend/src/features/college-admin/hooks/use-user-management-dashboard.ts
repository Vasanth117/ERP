"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchUserManagementDashboardPage } from "@/features/college-admin/api/users";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useUserManagementDashboardPage(params: {
  date_range?: string;
  role_filter?: string;
  department_id?: string;
} = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.userManagementDashboard(params),
    queryFn: () => fetchUserManagementDashboardPage(params),
  });
}