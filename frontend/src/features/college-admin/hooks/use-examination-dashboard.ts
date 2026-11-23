"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchExaminationDashboardPage } from "@/features/college-admin/api/examinations";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { ExaminationDashboardPageQuery } from "@/features/college-admin/types/examination-dashboard";

export function useExaminationDashboardPage(params: ExaminationDashboardPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.examinationDashboardPage(params),
    queryFn: () => fetchExaminationDashboardPage(params),
  });
}