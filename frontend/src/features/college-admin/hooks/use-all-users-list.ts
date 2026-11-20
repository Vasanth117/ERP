"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchAllUsersListPage } from "@/features/college-admin/api/users";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useAllUsersListPage(params: {
  page?: number;
  search?: string;
  role_filter?: string;
  department_id?: string;
  status_filter?: string;
} = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.allUsersListPage(params),
    queryFn: () => fetchAllUsersListPage(params),
  });
}