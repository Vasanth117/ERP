import { apiRequest } from "@/lib/api/client";

import type { CommunicationSectionSubNav } from "@/features/college-admin/types/communication-section-sub-nav";

export function fetchCommunicationSectionSubNav(path: string) {
  const search = new URLSearchParams({ path });
  return apiRequest<CommunicationSectionSubNav>(
    `/college-admin/communication-administration/navigation/section-sub-nav?${search.toString()}`,
  );
}