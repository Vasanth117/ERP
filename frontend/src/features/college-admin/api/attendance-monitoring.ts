import { apiRequest } from "@/lib/api/client";

import type {
  AttendanceMonitoringPage,
  AttendanceMonitoringQuery,
} from "@/features/college-admin/types/attendance-monitoring";

function buildQuery(params?: AttendanceMonitoringQuery): string {
  if (!params) return "";
  const q = new URLSearchParams();
  if (params.page != null) q.set("page", String(params.page));
  if (params.page_size != null) q.set("page_size", String(params.page_size));
  const s = q.toString();
  return s ? `?${s}` : "";
}

export function fetchAttendanceMonitoringPage(params?: AttendanceMonitoringQuery) {
  return apiRequest<AttendanceMonitoringPage>(
    `/college-admin/attendance-administration/monitoring/page${buildQuery(params)}`,
  );
}

export function notifyFacultyMissingAttendance() {
  return apiRequest<{ notified_count: number }>(
    "/college-admin/attendance-administration/monitoring/notify-faculty",
    { method: "POST" },
  );
}