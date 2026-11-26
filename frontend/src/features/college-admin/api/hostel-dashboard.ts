import { apiRequest } from "@/lib/api/client";

import type { HostelDashboardPage, HostelDashboardPageQuery } from "@/features/college-admin/types/hostel-dashboard";

export function fetchHostelDashboardPage(params?: HostelDashboardPageQuery) {
  const qs = new URLSearchParams();
  if (params?.page) qs.set("page", String(params.page));
  if (params?.page_size) qs.set("page_size", String(params.page_size));
  const suffix = qs.size ? `?${qs.toString()}` : "";
  return apiRequest<HostelDashboardPage>(`/college-admin/hostel-administration/dashboard/page${suffix}`);
}