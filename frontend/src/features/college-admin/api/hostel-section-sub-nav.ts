import { apiRequest } from "@/lib/api/client";

import type { HostelSectionSubNav } from "@/features/college-admin/types/hostel-section-sub-nav";

export function fetchHostelSectionSubNav(path: string) {
  const qs = new URLSearchParams({ path });
  return apiRequest<HostelSectionSubNav>(
    `/college-admin/hostel-administration/navigation/section-sub-nav?${qs.toString()}`,
  );
}