import { apiRequest } from "@/lib/api/client";

import type { ApiPage } from "@/features/student/types/common";
import type {
  NotificationSummary,
  StudentActivity,
  StudentDashboard,
  StudentDashboardStats,
} from "@/features/student/types/dashboard";
import type { PendingTaskSummary } from "@/features/student/types/dashboard";
import { pageQuery } from "@/features/student/api/pagination";

const BASE = "/students";

export async function fetchStudentDashboard(range = "week"): Promise<StudentDashboard> {
  const q = new URLSearchParams({ range });
  return apiRequest<StudentDashboard>(`${BASE}/me/dashboard?${q}`);
}

export async function fetchStudentDashboardStats(): Promise<StudentDashboardStats> {
  return apiRequest<StudentDashboardStats>(`${BASE}/me/dashboard/statistics`);
}

export async function fetchDashboardActivities(
  limit = 20,
  offset = 0,
): Promise<ApiPage<StudentActivity>> {
  return apiRequest<ApiPage<StudentActivity>>(
    `${BASE}/me/dashboard/activities?${pageQuery(limit, offset)}`,
  );
}

export async function fetchDashboardPendingTasks(): Promise<PendingTaskSummary[]> {
  return apiRequest<PendingTaskSummary[]>(`${BASE}/me/dashboard/pending-tasks`);
}

export async function fetchDashboardNotifications(
  limit = 20,
  offset = 0,
): Promise<ApiPage<NotificationSummary>> {
  return apiRequest<ApiPage<NotificationSummary>>(
    `${BASE}/me/dashboard/notifications?${pageQuery(limit, offset)}`,
  );
}