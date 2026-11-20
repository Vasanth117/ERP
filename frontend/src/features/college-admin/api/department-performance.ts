import { apiRequest } from "@/lib/api/client";

import type {
  DepartmentPerformanceOverview,
  DepartmentPerformanceQuery,
} from "@/features/college-admin/types/department-performance";

function buildQuery(params?: DepartmentPerformanceQuery): string {
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

export async function fetchDepartmentPerformanceOverview(
  params?: DepartmentPerformanceQuery,
): Promise<DepartmentPerformanceOverview> {
  return apiRequest<DepartmentPerformanceOverview>(
    `/college-admin/dashboard/department-performance${buildQuery(params)}`,
  );
}