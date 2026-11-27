import { apiRequest } from "@/lib/api/client";

import type {
  CommunicationFacultyNotificationsPage,
  CommunicationParentCommunicationPage,
  CommunicationStudentNotificationsPage,
} from "@/features/college-admin/types/communication-audience-notifications";

function buildQuery(page?: number, page_size?: number) {
  const search = new URLSearchParams();
  if (page != null) search.set("page", String(page));
  if (page_size != null) search.set("page_size", String(page_size));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchCommunicationStudentNotificationsPage(params?: { page?: number; page_size?: number }) {
  return apiRequest<CommunicationStudentNotificationsPage>(
    `/college-admin/communication-administration/audience/students/management/page${buildQuery(params?.page, params?.page_size)}`,
  );
}

export function fetchCommunicationFacultyNotificationsPage(params?: { page?: number; page_size?: number }) {
  return apiRequest<CommunicationFacultyNotificationsPage>(
    `/college-admin/communication-administration/audience/faculty/management/page${buildQuery(params?.page, params?.page_size)}`,
  );
}

export function fetchCommunicationParentCommunicationPage(params?: { page?: number; page_size?: number }) {
  return apiRequest<CommunicationParentCommunicationPage>(
    `/college-admin/communication-administration/audience/parents/management/page${buildQuery(params?.page, params?.page_size)}`,
  );
}