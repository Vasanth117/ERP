"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchReportsDashboardPage } from "@/features/college-admin/api/reports-dashboard";
import { fetchReportsSectionSubNav } from "@/features/college-admin/api/reports-section-sub-nav";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { ReportsDashboardPageQuery } from "@/features/college-admin/types/reports-dashboard";

export function useReportsDashboardPage(params?: ReportsDashboardPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.reportsDashboardPage(params),
    queryFn: () => fetchReportsDashboardPage(params),
  });
}

export function useReportsSectionSubNav(path: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.reportsSectionSubNav(path),
    queryFn: () => fetchReportsSectionSubNav(path),
    enabled: Boolean(path),
  });
}