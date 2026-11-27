import { apiRequest } from "@/lib/api/client";
import { apiBaseUrl } from "@/lib/env";
import { applyAuthHeaders } from "@/lib/api/auth-headers";

import type {
  CommunicationDeliveryStatusPage,
  CommunicationHistoryPage,
} from "@/features/college-admin/types/communication-delivery-history";

function buildQuery(params?: Record<string, string | number | undefined | null>) {
  const search = new URLSearchParams();
  if (!params) return "";
  for (const [key, value] of Object.entries(params)) {
    if (value != null && value !== "") search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchCommunicationDeliveryStatusPage(params?: { page?: number; page_size?: number }) {
  return apiRequest<CommunicationDeliveryStatusPage>(
    `/college-admin/communication-administration/deliveries/monitoring/page${buildQuery(params)}`,
  );
}

export function fetchCommunicationHistoryPage(params?: {
  page?: number;
  page_size?: number;
  search?: string;
  month?: string;
  channel?: string;
  sender?: string;
}) {
  return apiRequest<CommunicationHistoryPage>(
    `/college-admin/communication-administration/history/management/page${buildQuery(params)}`,
  );
}

export async function retryCommunicationFailedDeliveries() {
  return apiRequest<{ retried: number; skipped: number; failed_remaining: number }>(
    "/college-admin/communication-administration/deliveries/retry-failed",
    { method: "POST" },
  );
}

export async function downloadCommunicationHistoryExport(params?: {
  search?: string;
  month?: string;
  channel?: string;
  sender?: string;
}) {
  const path = `/college-admin/communication-administration/history/export${buildQuery(params)}`;
  const headers = new Headers();
  applyAuthHeaders(headers);
  const response = await fetch(`${apiBaseUrl()}${path}`, {
    method: "GET",
    headers,
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Export failed (${response.status})`);
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "communication-history.csv";
  a.click();
  URL.revokeObjectURL(url);
}