"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchRevaluationManagementPage } from "@/features/college-admin/api/examinations";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { RevaluationManagementPageQuery } from "@/features/college-admin/types/revaluation-management";

export function useRevaluationManagementPage(params: RevaluationManagementPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.revaluationManagementPage(params),
    queryFn: () => fetchRevaluationManagementPage(params),
  });
}