import { apiRequest } from "@/lib/api/client";

import type {
  LibraryCirculationIssueReturnPage,
  LibraryCirculationIssueReturnPageQuery,
} from "@/features/college-admin/types/library-circulation-issue-return";

function buildQuery(params?: LibraryCirculationIssueReturnPageQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.page_size != null) search.set("page_size", String(params.page_size));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchLibraryCirculationIssueReturnPage(params?: LibraryCirculationIssueReturnPageQuery) {
  return apiRequest<LibraryCirculationIssueReturnPage>(
    `/college-admin/library-administration/circulation/management/page${buildQuery(params)}`,
  );
}