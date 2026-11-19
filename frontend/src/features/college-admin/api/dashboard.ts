import { apiRequest } from "@/lib/api/client";

import type {
  ActivitySummary,
  ApiPage,
  CollegeDashboardOverview,
  DashboardDateRange,
  HeadcountStatistics,
  OperationalSummariesRead,
  PendingApprovalItem,
} from "@/features/college-admin/types/dashboard";

export type DashboardQuery = {
  range?: DashboardDateRange;
  anchor_date?: string;
  department_id?: string;
  campus_id?: string;
  academic_year_label?: string;
};

function toSearch(params: DashboardQuery): string {
  const q = new URLSearchParams();
  if (params.range) q.set("range", params.range);
  if (params.anchor_date) q.set("anchor_date", params.anchor_date);
  if (params.department_id) q.set("department_id", params.department_id);
  if (params.campus_id) q.set("campus_id", params.campus_id);
  if (params.academic_year_label) {
    q.set("academic_year_label", params.academic_year_label);
  }
  const s = q.toString();
  return s ? `?${s}` : "";
}

export async function fetchDashboardOverview(
  params: DashboardQuery = {},
): Promise<CollegeDashboardOverview> {
  return apiRequest<CollegeDashboardOverview>(
    `/college-admin/dashboard${toSearch(params)}`,
  );
}

export async function fetchDashboardStatistics(params: {
  department_id?: string;
  academic_year_label?: string;
} = {}): Promise<{ academic_term: CollegeDashboardOverview["academic_term"]; statistics: HeadcountStatistics }> {
  const q = new URLSearchParams();
  if (params.department_id) q.set("department_id", params.department_id);
  if (params.academic_year_label) {
    q.set("academic_year_label", params.academic_year_label);
  }
  const suffix = q.toString() ? `?${q}` : "";
  return apiRequest(`/college-admin/dashboard/statistics${suffix}`);
}

export async function fetchOperationalSummaries(params: {
  academic_year_label?: string;
} = {}): Promise<OperationalSummariesRead> {
  const q = new URLSearchParams();
  if (params.academic_year_label) {
    q.set("academic_year_label", params.academic_year_label);
  }
  const suffix = q.toString() ? `?${q}` : "";
  return apiRequest(`/college-admin/dashboard/operations${suffix}`);
}

export async function fetchPendingApprovals(
  offset = 0,
  limit = 20,
): Promise<ApiPage<PendingApprovalItem>> {
  return apiRequest(
    `/college-admin/dashboard/pending-approvals?limit=${limit}&offset=${offset}`,
  );
}

export async function fetchRecentActivities(
  offset = 0,
  limit = 20,
  range: DashboardDateRange = "week",
): Promise<ApiPage<ActivitySummary>> {
  return apiRequest(
    `/college-admin/dashboard/activities?limit=${limit}&offset=${offset}&range=${range}`,
  );
}