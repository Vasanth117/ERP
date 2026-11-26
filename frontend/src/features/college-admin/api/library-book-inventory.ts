import { apiRequest } from "@/lib/api/client";

import type {
  LibraryBookInventoryPage,
  LibraryBookInventoryPageQuery,
} from "@/features/college-admin/types/library-book-inventory";

function buildQuery(params?: LibraryBookInventoryPageQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.page_size != null) search.set("page_size", String(params.page_size));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchLibraryBookInventoryPage(params?: LibraryBookInventoryPageQuery) {
  return apiRequest<LibraryBookInventoryPage>(
    `/college-admin/library-administration/inventory/management/page${buildQuery(params)}`,
  );
}