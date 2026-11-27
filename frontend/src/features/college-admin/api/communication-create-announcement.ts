import { apiRequest } from "@/lib/api/client";

import type {
  CommunicationCreateAnnouncementFormValues,
  CommunicationCreateAnnouncementPage,
} from "@/features/college-admin/types/communication-create-announcement";

function buildQuery(
  announcementId?: string,
  audience?: string,
  presetChannels?: string,
  publishTiming?: string,
) {
  const search = new URLSearchParams();
  if (announcementId) search.set("announcement_id", announcementId);
  if (audience) search.set("audience", audience);
  if (presetChannels) search.set("preset_channels", presetChannels);
  if (publishTiming) search.set("publish_timing", publishTiming);
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchCommunicationCreateAnnouncementPage(
  announcementId?: string,
  audience?: string,
  presetChannels?: string,
  publishTiming?: string,
) {
  return apiRequest<CommunicationCreateAnnouncementPage>(
    `/college-admin/communication-administration/announcements/create/page${buildQuery(
      announcementId,
      audience,
      presetChannels,
      publishTiming,
    )}`,
  );
}

export function saveCommunicationCreateAnnouncementPage(
  action: "draft" | "publish",
  form: CommunicationCreateAnnouncementFormValues,
) {
  return apiRequest<CommunicationCreateAnnouncementPage>(
    "/college-admin/communication-administration/announcements/create/page",
    { method: "PUT", body: { action, form } },
  );
}