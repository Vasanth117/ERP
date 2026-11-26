import { apiRequest } from "@/lib/api/client";

import type {
  LibraryDigitalLibraryPage,
  LibraryDigitalLibraryPageQuery,
} from "@/features/college-admin/types/library-digital-library";

function buildQuery(params?: LibraryDigitalLibraryPageQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.page_size != null) search.set("page_size", String(params.page_size));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchLibraryDigitalLibraryPage(params?: LibraryDigitalLibraryPageQuery) {
  return apiRequest<LibraryDigitalLibraryPage>(
    `/college-admin/library-administration/digital/management/page${buildQuery(params)}`,
  );
}