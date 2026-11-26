"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import {
  fetchHrEmployeeOnboardingPage,
  fetchHrRecruitmentManagementPage,
} from "@/features/college-admin/api/hr-recruitment";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { HrRecruitmentPageQuery } from "@/features/college-admin/types/hr-recruitment";

export function useHrRecruitmentManagementPage(params?: HrRecruitmentPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hrRecruitmentManagementPage(params),
    queryFn: () => fetchHrRecruitmentManagementPage(params),
  });
}

export function useHrEmployeeOnboardingPage(params?: HrRecruitmentPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hrEmployeeOnboardingPage(params),
    queryFn: () => fetchHrEmployeeOnboardingPage(params),
  });
}