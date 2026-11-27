import { apiRequest } from "@/lib/api/client";

import type { LmsSectionSubNav } from "@/features/college-admin/types/lms-section-sub-nav";

export function fetchLmsSectionSubNav(path: string) {
  const qs = new URLSearchParams({ path });
  return apiRequest<LmsSectionSubNav>(
    `/college-admin/lms-administration/navigation/section-sub-nav?${qs.toString()}`,
  );
}