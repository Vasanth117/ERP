import { apiRequest } from "@/lib/api/client";
import { apiBaseUrl } from "@/lib/env";
import { applyAuthHeaders } from "@/lib/api/auth-headers";

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

export async function downloadFinanceDashboardExport(params?: FinanceDashboardPageQuery) {
  const path = `/college-admin/finance-administration/dashboard/export${buildQuery(params)}`;
  const headers = new Headers();
  applyAuthHeaders(headers);
  const response = await fetch(`${apiBaseUrl()}${path}`, {
    method: "GET",
    headers,
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Export failed (${response.status})`);
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "finance-dashboard.csv";
  a.click();
  URL.revokeObjectURL(url);
}