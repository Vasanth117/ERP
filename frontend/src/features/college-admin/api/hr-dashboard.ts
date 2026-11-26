import { apiRequest } from "@/lib/api/client";

import type { HrDashboardPage, HrDashboardPageQuery } from "@/features/college-admin/types/hr-dashboard";

function buildHrDashboardQuery(params?: HrDashboardPageQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.page_size != null) search.set("page_size", String(params.page_size));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchHrDashboardPage(params?: HrDashboardPageQuery) {
  return apiRequest<HrDashboardPage>(
    `/college-admin/hr-administration/dashboard/page${buildHrDashboardQuery(params)}`,
  );
}