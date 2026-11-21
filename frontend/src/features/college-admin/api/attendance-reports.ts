import { apiRequest } from "@/lib/api/client";

import type {
  AttendanceReportCreatePayload,
  AttendanceReportsPage,
  AttendanceReportsQuery,
} from "@/features/college-admin/types/attendance-reports";

function buildQuery(params?: AttendanceReportsQuery): string {
  if (!params) return "";
  const q = new URLSearchParams();
  if (params.page != null) q.set("page", String(params.page));
  if (params.page_size != null) q.set("page_size", String(params.page_size));
  const s = q.toString();
  return s ? `?${s}` : "";
}

export function fetchAttendanceReportsPage(params?: AttendanceReportsQuery) {
  return apiRequest<AttendanceReportsPage>(
    `/college-admin/attendance-administration/reports/page${buildQuery(params)}`,
  );
}

export function createAttendanceReport(payload: AttendanceReportCreatePayload) {
  return apiRequest<AttendanceReportsPage>("/college-admin/attendance-administration/reports/create", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}