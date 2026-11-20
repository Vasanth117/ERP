import { apiRequest } from "@/lib/api/client";

import type {
  AttendanceOverview,
  AttendanceOverviewQuery,
} from "@/features/college-admin/types/attendance-overview";

function buildQuery(params?: AttendanceOverviewQuery): string {
  if (!params) return "";
  const q = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      q.set(key, value);
    }
  });
  const s = q.toString();
  return s ? `?${s}` : "";
}

export async function fetchAttendanceOverview(
  params?: AttendanceOverviewQuery,
): Promise<AttendanceOverview> {
  return apiRequest<AttendanceOverview>(
    `/college-admin/dashboard/attendance-overview${buildQuery(params)}`,
  );
}