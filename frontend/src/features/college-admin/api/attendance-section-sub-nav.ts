import { apiRequest } from "@/lib/api/client";

import type { AttendanceSectionSubNav } from "@/features/college-admin/types/attendance-section-sub-nav";

export function fetchAttendanceSectionSubNav(path: string) {
  const qs = new URLSearchParams({ path });
  return apiRequest<AttendanceSectionSubNav>(
    `/college-admin/attendance-administration/navigation/section-sub-nav?${qs.toString()}`,
  );
}