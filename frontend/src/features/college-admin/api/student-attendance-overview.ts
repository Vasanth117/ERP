import { apiRequest } from "@/lib/api/client";

import type {
  StudentAttendanceOverviewPage,
  StudentAttendanceOverviewQuery,
} from "@/features/college-admin/types/student-attendance-overview";

function buildQuery(params?: StudentAttendanceOverviewQuery): string {
  if (!params) return "";
  const q = new URLSearchParams();
  if (params.term_key) q.set("term_key", params.term_key);
  if (params.programme_code) q.set("programme_code", params.programme_code);
  const s = q.toString();
  return s ? `?${s}` : "";
}

export function fetchStudentAttendanceOverviewPage(params?: StudentAttendanceOverviewQuery) {
  return apiRequest<StudentAttendanceOverviewPage>(
    `/college-admin/attendance-administration/student-attendance/page${buildQuery(params)}`,
  );
}