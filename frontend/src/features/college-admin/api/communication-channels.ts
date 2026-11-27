import { apiRequest } from "@/lib/api/client";

import type {
  CommunicationEmailChannelPage,
  CommunicationSmsChannelPage,
  CommunicationWhatsappChannelPage,
} from "@/features/college-admin/types/communication-channels";

function buildQuery(page?: number, page_size?: number) {
  const search = new URLSearchParams();
  if (page != null) search.set("page", String(page));
  if (page_size != null) search.set("page_size", String(page_size));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchCommunicationEmailChannelPage(params?: { page?: number; page_size?: number }) {
  return apiRequest<CommunicationEmailChannelPage>(
    `/college-admin/communication-administration/channels/email/management/page${buildQuery(params?.page, params?.page_size)}`,
  );
}

export function fetchCommunicationSmsChannelPage(params?: { page?: number; page_size?: number }) {
  return apiRequest<CommunicationSmsChannelPage>(
    `/college-admin/communication-administration/channels/sms/management/page${buildQuery(params?.page, params?.page_size)}`,
  );
}

export function fetchCommunicationWhatsappChannelPage(params?: { page?: number; page_size?: number }) {
  return apiRequest<CommunicationWhatsappChannelPage>(
    `/college-admin/communication-administration/channels/whatsapp/management/page${buildQuery(params?.page, params?.page_size)}`,
  );
}