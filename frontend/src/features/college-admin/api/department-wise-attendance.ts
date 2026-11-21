import { apiRequest } from "@/lib/api/client";

import type {
  DepartmentWiseAttendancePage,
  DepartmentWiseAttendanceQuery,
} from "@/features/college-admin/types/department-wise-attendance";

function buildQuery(params?: DepartmentWiseAttendanceQuery): string {
  if (!params?.term_key) return "";
  return `?term_key=${encodeURIComponent(params.term_key)}`;
}

export function fetchDepartmentWiseAttendancePage(params?: DepartmentWiseAttendanceQuery) {
  return apiRequest<DepartmentWiseAttendancePage>(
    `/college-admin/attendance-administration/department-wise/page${buildQuery(params)}`,
  );
}