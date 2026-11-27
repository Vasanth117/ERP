import { apiRequest } from "@/lib/api/client";

import type {
  AttendanceConfigurationPage,
  AttendanceConfigurationSavePayload,
  AttendanceInstitutionalPolicySavePayload,
  AttendanceRulesPoliciesPage,
  AttendanceRulesPoliciesQuery,
} from "@/features/college-admin/types/attendance-configuration";

export function fetchAttendanceConfigurationPage() {
  return apiRequest<AttendanceConfigurationPage>("/college-admin/attendance-administration/configuration/page");
}

export function saveAttendanceConfiguration(payload: AttendanceConfigurationSavePayload) {
  return apiRequest<AttendanceConfigurationPage>("/college-admin/attendance-administration/configuration/save", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

function buildPoliciesQuery(params?: AttendanceRulesPoliciesQuery): string {
  if (!params) return "";
  const q = new URLSearchParams();
  if (params.page != null) q.set("page", String(params.page));
  if (params.page_size != null) q.set("page_size", String(params.page_size));
  const s = q.toString();
  return s ? `?${s}` : "";
}

export function fetchAttendanceRulesPoliciesPage(params?: AttendanceRulesPoliciesQuery) {
  return apiRequest<AttendanceRulesPoliciesPage>(
    `/college-admin/attendance-administration/rules-policies/page${buildPoliciesQuery(params)}`,
  );
}

export function saveAttendanceInstitutionalPolicy(
  payload: AttendanceInstitutionalPolicySavePayload,
  params?: AttendanceRulesPoliciesQuery,
) {
  return apiRequest<AttendanceRulesPoliciesPage>(
    `/college-admin/attendance-administration/rules-policies/save${buildPoliciesQuery(params)}`,
    { method: "POST", body: payload },
  );
}