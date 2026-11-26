import { apiRequest } from "@/lib/api/client";

import type { HostelReportsPage, HostelReportsPageQuery } from "@/features/college-admin/types/hostel-reports";

function buildQuery(params?: HostelReportsPageQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.page_size != null) search.set("page_size", String(params.page_size));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchHostelReportsPage(params?: HostelReportsPageQuery) {
  return apiRequest<HostelReportsPage>(
    `/college-admin/hostel-administration/reports/management/page${buildQuery(params)}`,
  );
}