import { apiRequest } from "@/lib/api/client";

import type {
  LibraryBookCataloguePage,
  LibraryBookCataloguePageQuery,
} from "@/features/college-admin/types/library-book-catalogue";

function buildQuery(params?: LibraryBookCataloguePageQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.page_size != null) search.set("page_size", String(params.page_size));
  if (params?.search) search.set("search", params.search);
  if (params?.category) search.set("category", params.category);
  if (params?.branch_code) search.set("branch_code", params.branch_code);
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchLibraryBookCataloguePage(params?: LibraryBookCataloguePageQuery) {
  return apiRequest<LibraryBookCataloguePage>(
    `/college-admin/library-administration/catalogue/management/page${buildQuery(params)}`,
  );
}