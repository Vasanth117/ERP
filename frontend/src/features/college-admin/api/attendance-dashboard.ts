import { apiRequest } from "@/lib/api/client";

import type {
  AttendanceDashboardPage,
  AttendanceDashboardQuery,
} from "@/features/college-admin/types/attendance-dashboard";

function buildQuery(params?: AttendanceDashboardQuery): string {
  if (!params) return "";
  const q = new URLSearchParams();
  if (params.term_key) q.set("term_key", params.term_key);
  if (params.department_id) q.set("department_id", params.department_id);
  const s = q.toString();
  return s ? `?${s}` : "";
}

export function fetchAttendanceDashboardPage(params?: AttendanceDashboardQuery) {
  return apiRequest<AttendanceDashboardPage>(
    `/college-admin/attendance-administration/dashboard/page${buildQuery(params)}`,
  );
}