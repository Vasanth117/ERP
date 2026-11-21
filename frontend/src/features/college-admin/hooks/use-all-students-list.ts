"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchAllStudentsListPage } from "@/features/college-admin/api/students";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useAllStudentsListPage(
  params: {
    page?: number;
    search?: string;
    programme_code?: string;
    study_year?: string;
    section_code?: string;
    status_filter?: string;
  } = {},
) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.allStudentsListPage(params),
    queryFn: () => fetchAllStudentsListPage(params),
  });
}