import { apiRequest } from "@/lib/api/client";

import type {
  FacultyStatisticsOverview,
  FacultyStatisticsQuery,
} from "@/features/college-admin/types/faculty-statistics";

function buildQuery(params?: FacultyStatisticsQuery): string {
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

export async function fetchFacultyStatisticsOverview(
  params?: FacultyStatisticsQuery,
): Promise<FacultyStatisticsOverview> {
  return apiRequest<FacultyStatisticsOverview>(
    `/college-admin/dashboard/faculty-statistics${buildQuery(params)}`,
  );
}