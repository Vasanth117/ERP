import { apiRequest } from "@/lib/api/client";

import type {
  LibraryMemberManagementPage,
  LibraryMemberManagementPageQuery,
} from "@/features/college-admin/types/library-member-management";

function buildQuery(params?: LibraryMemberManagementPageQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.page_size != null) search.set("page_size", String(params.page_size));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchLibraryMemberManagementPage(params?: LibraryMemberManagementPageQuery) {
  return apiRequest<LibraryMemberManagementPage>(
    `/college-admin/library-administration/members/management/page${buildQuery(params)}`,
  );
}