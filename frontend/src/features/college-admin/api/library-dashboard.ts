import { apiRequest } from "@/lib/api/client";

import type {
  LibraryDashboardPage,
  LibraryDashboardPageQuery,
} from "@/features/college-admin/types/library-dashboard";

function buildLibraryDashboardQuery(params?: LibraryDashboardPageQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.page_size != null) search.set("page_size", String(params.page_size));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchLibraryDashboardPage(params?: LibraryDashboardPageQuery) {
  return apiRequest<LibraryDashboardPage>(
    `/college-admin/library-administration/dashboard/page${buildLibraryDashboardQuery(params)}`,
  );
}