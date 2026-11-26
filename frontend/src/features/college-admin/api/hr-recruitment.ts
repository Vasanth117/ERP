import { apiRequest } from "@/lib/api/client";

import type {
  HrEmployeeOnboardingPage,
  HrRecruitmentManagementPage,
  HrRecruitmentPageQuery,
} from "@/features/college-admin/types/hr-recruitment";

function buildQuery(params?: HrRecruitmentPageQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.page_size != null) search.set("page_size", String(params.page_size));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchHrRecruitmentManagementPage(params?: HrRecruitmentPageQuery) {
  return apiRequest<HrRecruitmentManagementPage>(
    `/college-admin/hr-administration/recruitment/management/page${buildQuery(params)}`,
  );
}

export function fetchHrEmployeeOnboardingPage(params?: HrRecruitmentPageQuery) {
  return apiRequest<HrEmployeeOnboardingPage>(
    `/college-admin/hr-administration/onboarding/management/page${buildQuery(params)}`,
  );
}