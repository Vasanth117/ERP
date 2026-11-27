import { apiRequest } from "@/lib/api/client";

import type {
  CommunicationScheduledMessagesPage,
  CommunicationTemplatesManagementPage,
} from "@/features/college-admin/types/communication-templates-scheduling";

function buildQuery(page?: number, page_size?: number) {
  const search = new URLSearchParams();
  if (page != null) search.set("page", String(page));
  if (page_size != null) search.set("page_size", String(page_size));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchCommunicationTemplatesManagementPage(params?: { page?: number; page_size?: number }) {
  return apiRequest<CommunicationTemplatesManagementPage>(
    `/college-admin/communication-administration/templates/management/page${buildQuery(params?.page, params?.page_size)}`,
  );
}

export function fetchCommunicationScheduledMessagesPage(params?: { page?: number; page_size?: number }) {
  return apiRequest<CommunicationScheduledMessagesPage>(
    `/college-admin/communication-administration/scheduled/management/page${buildQuery(params?.page, params?.page_size)}`,
  );
}