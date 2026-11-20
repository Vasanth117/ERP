"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchDepartmentStatusHistoryPage } from "@/features/college-admin/api/organization";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useDepartmentStatusHistoryPage(params?: {
  page?: number;
  since_year?: string;
  department_id?: string;
  change_type_filter?: string;
  selected_department_id?: string;
}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.departmentStatusHistoryPage(params),
    queryFn: () => fetchDepartmentStatusHistoryPage(params),
  });
}