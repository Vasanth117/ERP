import { apiRequest } from "@/lib/api/client";

import type {
  LmsReportsPage,
  LmsReportsPageQuery,
  LmsSettingsFormValues,
  LmsSettingsPage,
} from "@/features/college-admin/types/lms-reports-settings";

function buildQuery(params?: LmsReportsPageQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.page_size != null) search.set("page_size", String(params.page_size));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchLmsReportsPage(params?: LmsReportsPageQuery) {
  return apiRequest<LmsReportsPage>(
    `/college-admin/lms-administration/reports/management/page${buildQuery(params)}`,
  );
}

export function createLmsReportSchedule(report_key: string, params?: LmsReportsPageQuery) {
  return apiRequest<LmsReportsPage>(
    `/college-admin/lms-administration/reports/management/page${buildQuery(params)}`,
    { method: "POST", body: JSON.stringify({ report_key }) },
  );
}

export function fetchLmsSettingsPage() {
  return apiRequest<LmsSettingsPage>("/college-admin/lms-administration/settings/management/page");
}

export function saveLmsSettingsPage(form: LmsSettingsFormValues) {
  return apiRequest<LmsSettingsPage>("/college-admin/lms-administration/settings/management/page", {
    method: "PUT",
    body: JSON.stringify({ form }),
  });
}