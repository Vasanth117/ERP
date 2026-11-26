import { apiRequest } from "@/lib/api/client";

import type {
  HrReportScheduleCreate,
  HrReportsPage,
  HrReportsPageQuery,
  HrSettingsPoliciesFormValues,
  HrSettingsPoliciesPage,
} from "@/features/college-admin/types/hr-reports-settings";

function buildQuery(params?: HrReportsPageQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.page_size != null) search.set("page_size", String(params.page_size));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchHrReportsPage(params?: HrReportsPageQuery) {
  return apiRequest<HrReportsPage>(`/college-admin/hr-administration/reports/page${buildQuery(params)}`);
}

export function createHrReportSchedule(body: HrReportScheduleCreate, params?: HrReportsPageQuery) {
  return apiRequest<HrReportsPage>(
    `/college-admin/hr-administration/reports/schedules${buildQuery(params)}`,
    { method: "POST", body: JSON.stringify(body) },
  );
}

export function fetchHrSettingsPoliciesPage() {
  return apiRequest<HrSettingsPoliciesPage>("/college-admin/hr-administration/settings/policies/page");
}

export function saveHrSettingsPoliciesPage(form: HrSettingsPoliciesFormValues) {
  return apiRequest<HrSettingsPoliciesPage>("/college-admin/hr-administration/settings/policies/page", {
    method: "PUT",
    body: JSON.stringify({ form }),
  });
}