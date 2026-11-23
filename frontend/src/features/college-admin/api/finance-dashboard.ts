import { apiRequest } from "@/lib/api/client";

import type { FinanceDashboardPage, FinanceDashboardPageQuery } from "@/features/college-admin/types/finance-dashboard";

function buildQuery(params?: FinanceDashboardPageQuery): string {
  const search = new URLSearchParams();
  if (params?.page) search.set("page", String(params.page));
  if (params?.academic_year_code) search.set("academic_year_code", params.academic_year_code);
  if (params?.programme_code) search.set("programme_code", params.programme_code);
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchFinanceDashboardPage(params?: FinanceDashboardPageQuery) {
  return apiRequest<FinanceDashboardPage>(
    `/college-admin/finance-administration/dashboard/page${buildQuery(params)}`,
  );
}