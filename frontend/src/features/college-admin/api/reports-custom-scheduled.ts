import { apiRequest } from "@/lib/api/client";

import type {
  ReportsBuilderPageQuery,
  ReportsCustomBuilderPage,
  ReportsCustomBuilderSave,
  ReportsExportHistoryPage,
  ReportsPageQuery,
  ReportsScheduleCreate,
  ReportsScheduledPage,
} from "@/features/college-admin/types/reports-custom-scheduled";

function buildQuery(params?: Record<string, string | number | undefined>) {
  const search = new URLSearchParams();
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value != null && value !== "") search.set(key, String(value));
    }
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchReportsScheduledPage(params?: ReportsPageQuery) {
  return apiRequest<ReportsScheduledPage>(
    `/college-admin/reports-analytics/custom-scheduled/scheduled/management/page${buildQuery(params)}`,
  );
}

export function fetchReportsExportHistoryPage(params?: ReportsPageQuery) {
  return apiRequest<ReportsExportHistoryPage>(
    `/college-admin/reports-analytics/custom-scheduled/exports/management/page${buildQuery(params)}`,
  );
}

export function fetchReportsCustomBuilderPage(params?: ReportsBuilderPageQuery) {
  return apiRequest<ReportsCustomBuilderPage>(
    `/college-admin/reports-analytics/custom-scheduled/builder/management/page${buildQuery(params)}`,
  );
}

export function saveReportsCustomBuilder(body: ReportsCustomBuilderSave, params?: ReportsBuilderPageQuery) {
  return apiRequest<ReportsCustomBuilderPage>(
    `/college-admin/reports-analytics/custom-scheduled/builder/management/page${buildQuery(params)}`,
    { method: "PUT", body: JSON.stringify(body) },
  );
}

export function createReportsSchedule(body: ReportsScheduleCreate) {
  return apiRequest<{ job_id: string; report_key: string; status: string }>(
    "/college-admin/reports-analytics/schedule",
    {
      method: "POST",
      body: JSON.stringify({
        report_key: body.report_key,
        schedule_cron: body.schedule_cron ?? "0 7 * * 1",
        frequency_label: body.frequency_label ?? "Weekly",
        export_format: body.export_format ?? "excel",
        recipients: body.recipients ?? [],
        paused: false,
      }),
    },
  );
}

export function runReportsGenerate(report_key: string) {
  return apiRequest<{ job_id: string; report_key: string; status: string }>(
    "/college-admin/reports-analytics/generate",
    { method: "POST", body: JSON.stringify({ report_key }) },
  );
}