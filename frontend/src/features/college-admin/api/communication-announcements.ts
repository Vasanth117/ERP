import { apiRequest } from "@/lib/api/client";

import type {
  CommunicationAnnouncementsManagementPage,
  CommunicationAnnouncementsPageQuery,
} from "@/features/college-admin/types/communication-announcements";

function buildQuery(params?: CommunicationAnnouncementsPageQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.page_size != null) search.set("page_size", String(params.page_size));
  if (params?.search) search.set("search", params.search);
  if (params?.audience) search.set("audience", params.audience);
  if (params?.status) search.set("status", params.status);
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchCommunicationAnnouncementsPage(params?: CommunicationAnnouncementsPageQuery) {
  return apiRequest<CommunicationAnnouncementsManagementPage>(
    `/college-admin/communication-administration/announcements/management/page${buildQuery(params)}`,
  );
}