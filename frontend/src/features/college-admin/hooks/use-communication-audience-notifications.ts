"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import {
  fetchCommunicationFacultyNotificationsPage,
  fetchCommunicationParentCommunicationPage,
  fetchCommunicationStudentNotificationsPage,
} from "@/features/college-admin/api/communication-audience-notifications";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useCommunicationStudentNotificationsPage(
  params?: { page?: number; page_size?: number },
  enabled = true,
) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.communicationStudentNotificationsPage(params),
    queryFn: () => fetchCommunicationStudentNotificationsPage(params),
    enabled,
  });
}

export function useCommunicationFacultyNotificationsPage(
  params?: { page?: number; page_size?: number },
  enabled = true,
) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.communicationFacultyNotificationsPage(params),
    queryFn: () => fetchCommunicationFacultyNotificationsPage(params),
    enabled,
  });
}

export function useCommunicationParentCommunicationPage(
  params?: { page?: number; page_size?: number },
  enabled = true,
) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.communicationParentCommunicationPage(params),
    queryFn: () => fetchCommunicationParentCommunicationPage(params),
    enabled,
  });
}