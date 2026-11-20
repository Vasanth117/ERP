import { apiRequest } from "@/lib/api/client";

import type {
  StudentStatisticsOverview,
  StudentStatisticsQuery,
} from "@/features/college-admin/types/student-statistics";

function buildQuery(params?: StudentStatisticsQuery): string {
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

export async function fetchStudentStatisticsOverview(
  params?: StudentStatisticsQuery,
): Promise<StudentStatisticsOverview> {
  return apiRequest<StudentStatisticsOverview>(
    `/college-admin/dashboard/student-statistics${buildQuery(params)}`,
  );
}