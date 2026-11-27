import { apiRequest } from "@/lib/api/client";

import type {
  CommunicationDashboardPage,
  CommunicationDashboardPageQuery,
} from "@/features/college-admin/types/communication-dashboard";

function buildQuery(params?: CommunicationDashboardPageQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.page_size != null) search.set("page_size", String(params.page_size));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchCommunicationDashboardPage(params?: CommunicationDashboardPageQuery) {
  return apiRequest<CommunicationDashboardPage>(
    `/college-admin/communication-administration/dashboard/page${buildQuery(params)}`,
  );
}