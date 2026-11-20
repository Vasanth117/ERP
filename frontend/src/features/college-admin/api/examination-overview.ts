import { apiRequest } from "@/lib/api/client";

import type {
  ExaminationOverview,
  ExaminationOverviewQuery,
} from "@/features/college-admin/types/examination-overview";

function buildQuery(params?: ExaminationOverviewQuery): string {
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

export async function fetchExaminationOverview(
  params?: ExaminationOverviewQuery,
): Promise<ExaminationOverview> {
  return apiRequest<ExaminationOverview>(
    `/college-admin/dashboard/examination-overview${buildQuery(params)}`,
  );
}