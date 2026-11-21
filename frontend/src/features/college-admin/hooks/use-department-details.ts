"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchDepartmentDetailsPage } from "@/features/college-admin/api/organization";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useDepartmentDetailsPage(departmentId: string | null) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.departmentDetailsPage(departmentId),
    queryFn: () => fetchDepartmentDetailsPage(departmentId!),
    enabled: Boolean(departmentId),
  });
}