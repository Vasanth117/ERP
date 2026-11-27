import { apiRequest } from "@/lib/api/client";

import type { LmsDashboardPage } from "@/features/college-admin/types/lms-dashboard";

function buildQuery(page?: number, page_size?: number) {
  const search = new URLSearchParams();
  if (page != null) search.set("page", String(page));
  if (page_size != null) search.set("page_size", String(page_size));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchLmsDashboardPage(params?: { page?: number; page_size?: number }) {
  return apiRequest<LmsDashboardPage>(
    `/college-admin/lms-administration/dashboard/page${buildQuery(params?.page, params?.page_size)}`,
  );
}