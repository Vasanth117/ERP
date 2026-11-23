"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchDepartmentManagementDashboardPage } from "@/features/college-admin/api/organization";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useDepartmentManagementDashboardPage(params?: {
  academic_year_label?: string;
  campus_id?: string;
  school_id?: string;
}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.departmentManagementDashboard(params),
    queryFn: () => fetchDepartmentManagementDashboardPage(params),
  });
}