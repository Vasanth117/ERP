"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchAllDepartmentsListPage } from "@/features/college-admin/api/organization";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useAllDepartmentsListPage(
  params: {
    page?: number;
    search?: string;
    school_id?: string;
    type_filter?: string;
    status_filter?: string;
  } = {},
) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.allDepartmentsListPage(params),
    queryFn: () => fetchAllDepartmentsListPage(params),
  });
}