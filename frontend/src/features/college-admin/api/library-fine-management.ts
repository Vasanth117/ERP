import { apiRequest } from "@/lib/api/client";

import type {
  LibraryFineManagementPage,
  LibraryFineManagementPageQuery,
} from "@/features/college-admin/types/library-fine-management";

function buildQuery(params?: LibraryFineManagementPageQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.page_size != null) search.set("page_size", String(params.page_size));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchLibraryFineManagementPage(params?: LibraryFineManagementPageQuery) {
  return apiRequest<LibraryFineManagementPage>(
    `/college-admin/library-administration/fines/management/page${buildQuery(params)}`,
  );
}