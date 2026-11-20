import { apiRequest } from "@/lib/api/client";

import type { AlertsOverview } from "@/features/college-admin/types/alerts-overview";

export async function fetchAlertsOverview(): Promise<AlertsOverview> {
  return apiRequest<AlertsOverview>("/college-admin/dashboard/alerts-overview");
}

export async function markAllAlertsRead(): Promise<{ marked: number }> {
  return apiRequest<{ marked: number }>("/college-admin/dashboard/alerts-overview/mark-read", {
    method: "POST",
    body: {},
  });
}