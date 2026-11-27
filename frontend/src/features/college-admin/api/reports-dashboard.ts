import { apiRequest } from "@/lib/api/client";

import type { ReportsDashboardPage, ReportsDashboardPageQuery } from "@/features/college-admin/types/reports-dashboard";

function buildQuery(params?: ReportsDashboardPageQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.page_size != null) search.set("page_size", String(params.page_size));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchReportsDashboardPage(params?: ReportsDashboardPageQuery) {
  return apiRequest<ReportsDashboardPage>(
    `/college-admin/reports-analytics/dashboard/management/page${buildQuery(params)}`,
  );
}