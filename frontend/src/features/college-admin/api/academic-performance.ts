import { apiRequest } from "@/lib/api/client";

import type {
  AcademicPerformanceOverview,
  AcademicPerformanceQuery,
} from "@/features/college-admin/types/academic-performance";

function buildQuery(params?: AcademicPerformanceQuery): string {
  if (!params) return "";
  const q = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") q.set(key, value);
  });
  const s = q.toString();
  return s ? `?${s}` : "";
}

export async function fetchAcademicPerformanceOverview(
  params?: AcademicPerformanceQuery,
): Promise<AcademicPerformanceOverview> {
  return apiRequest<AcademicPerformanceOverview>(
    `/college-admin/dashboard/academic-performance${buildQuery(params)}`,
  );
}