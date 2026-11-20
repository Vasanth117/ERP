"use client";

import { useQuery } from "@tanstack/react-query";

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