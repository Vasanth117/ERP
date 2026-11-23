"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchExaminationOverview } from "@/features/college-admin/api/examination-overview";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { ExaminationOverviewQuery } from "@/features/college-admin/types/examination-overview";

export function useExaminationOverview(params?: ExaminationOverviewQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.examinationOverview(params),
    queryFn: () => fetchExaminationOverview(params),
  });
}