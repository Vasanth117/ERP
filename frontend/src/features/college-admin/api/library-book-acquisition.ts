import { apiRequest } from "@/lib/api/client";

import type {
  LibraryBookAcquisitionPage,
  LibraryBookAcquisitionPageQuery,
} from "@/features/college-admin/types/library-book-acquisition";

function buildQuery(params?: LibraryBookAcquisitionPageQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.page_size != null) search.set("page_size", String(params.page_size));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchLibraryBookAcquisitionPage(params?: LibraryBookAcquisitionPageQuery) {
  return apiRequest<LibraryBookAcquisitionPage>(
    `/college-admin/library-administration/acquisitions/management/page${buildQuery(params)}`,
  );
}