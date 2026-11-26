import { apiRequest } from "@/lib/api/client";

import type { LibrarySectionSubNav } from "@/features/college-admin/types/library-section-sub-nav";

export function fetchLibrarySectionSubNav(path: string) {
  const qs = new URLSearchParams({ path });
  return apiRequest<LibrarySectionSubNav>(
    `/college-admin/library-administration/navigation/section-sub-nav?${qs.toString()}`,
  );
}