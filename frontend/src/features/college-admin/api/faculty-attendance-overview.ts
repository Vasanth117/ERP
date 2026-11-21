import { apiRequest } from "@/lib/api/client";

import type {
  FacultyAttendanceOverviewPage,
  FacultyAttendanceOverviewQuery,
} from "@/features/college-admin/types/faculty-attendance-overview";

function buildQuery(params?: FacultyAttendanceOverviewQuery): string {
  if (!params) return "";
  const q = new URLSearchParams();
  if (params.department_id) q.set("department_id", params.department_id);
  if (params.page != null) q.set("page", String(params.page));
  if (params.page_size != null) q.set("page_size", String(params.page_size));
  const s = q.toString();
  return s ? `?${s}` : "";
}

export function fetchFacultyAttendanceOverviewPage(params?: FacultyAttendanceOverviewQuery) {
  return apiRequest<FacultyAttendanceOverviewPage>(
    `/college-admin/attendance-administration/faculty-attendance/page${buildQuery(params)}`,
  );
}