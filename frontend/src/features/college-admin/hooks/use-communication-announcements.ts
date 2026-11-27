"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchCommunicationAnnouncementsPage } from "@/features/college-admin/api/communication-announcements";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { CommunicationAnnouncementsPageQuery } from "@/features/college-admin/types/communication-announcements";

export function useCommunicationAnnouncementsPage(params?: CommunicationAnnouncementsPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.communicationAnnouncementsPage(params),
    queryFn: () => fetchCommunicationAnnouncementsPage(params),
  });
}