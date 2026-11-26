import { apiRequest } from "@/lib/api/client";

import type { LibraryReportsPage, LibraryReportsPageQuery } from "@/features/college-admin/types/library-reports";

function buildQuery(params?: LibraryReportsPageQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.page_size != null) search.set("page_size", String(params.page_size));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchLibraryReportsPage(params?: LibraryReportsPageQuery) {
  return apiRequest<LibraryReportsPage>(
    `/college-admin/library-administration/reports/management/page${buildQuery(params)}`,
  );
}