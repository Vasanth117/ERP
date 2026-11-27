import { apiRequest } from "@/lib/api/client";

import type { ReportsSectionSubNav } from "@/features/college-admin/types/reports-dashboard";

export function fetchReportsSectionSubNav(path: string) {
  const qs = new URLSearchParams({ path });
  return apiRequest<ReportsSectionSubNav>(
    `/college-admin/reports-analytics/navigation/section-sub-nav?${qs.toString()}`,
  );
}