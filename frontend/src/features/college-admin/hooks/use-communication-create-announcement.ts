"use client";

import { useQueryClient } from "@tanstack/react-query";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useCollegeAdminMutation as useMutation } from "@/features/college-admin/hooks/use-college-admin-mutation";

import {
  fetchCommunicationCreateAnnouncementPage,
  saveCommunicationCreateAnnouncementPage,
} from "@/features/college-admin/api/communication-create-announcement";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { CommunicationCreateAnnouncementFormValues } from "@/features/college-admin/types/communication-create-announcement";

export function useCommunicationCreateAnnouncementPage(
  announcementId?: string,
  audience?: string,
  presetChannels?: string,
  publishTiming?: string,
) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.communicationCreateAnnouncementPage(
      announcementId,
      audience,
      presetChannels,
      publishTiming,
    ),
    queryFn: () =>
      fetchCommunicationCreateAnnouncementPage(announcementId, audience, presetChannels, publishTiming),
  });
}

export function useSaveCommunicationCreateAnnouncementPage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      action,
      form,
    }: {
      action: "draft" | "publish";
      form: CommunicationCreateAnnouncementFormValues;
    }) => saveCommunicationCreateAnnouncementPage(action, form),
    onSuccess: (data) => {
      queryClient.setQueryData(
        collegeAdminQueryKeys.communicationCreateAnnouncementPage(data.form.announcement_id || undefined),
        data,
      );
      void queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.communicationAnnouncementsPage() });
    },
  });
}