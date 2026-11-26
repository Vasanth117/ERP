import { apiRequest } from "@/lib/api/client";

import type {
  LibraryLostDamagedPage,
  LibraryLostDamagedPageQuery,
} from "@/features/college-admin/types/library-lost-damaged";

function buildQuery(params?: LibraryLostDamagedPageQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.page_size != null) search.set("page_size", String(params.page_size));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchLibraryLostDamagedPage(params?: LibraryLostDamagedPageQuery) {
  return apiRequest<LibraryLostDamagedPage>(
    `/college-admin/library-administration/lost-damaged/management/page${buildQuery(params)}`,
  );
}