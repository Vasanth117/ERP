import { useCollegeAdminMutation as useMutation } from "@/features/college-admin/hooks/use-college-admin-mutation";
import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useQueryClient } from "@tanstack/react-query";

import {
  createHrReportSchedule,
  fetchHrReportsPage,
  fetchHrSettingsPoliciesPage,
  saveHrSettingsPoliciesPage,
} from "@/features/college-admin/api/hr-reports-settings";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type {
  HrReportScheduleCreate,
  HrReportsPageQuery,
  HrSettingsPoliciesFormValues,
} from "@/features/college-admin/types/hr-reports-settings";

export function useHrReportsPage(params?: HrReportsPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hrReportsPage(params),
    queryFn: () => fetchHrReportsPage(params),
  });
}

export function useCreateHrReportSchedule(listParams?: HrReportsPageQuery) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: HrReportScheduleCreate) => createHrReportSchedule(body, listParams),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.hrReportsPage() });
    },
  });
}

export function useHrSettingsPoliciesPage() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hrSettingsPoliciesPage(),
    queryFn: () => fetchHrSettingsPoliciesPage(),
  });
}

export function useSaveHrSettingsPoliciesPage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (form: HrSettingsPoliciesFormValues) => saveHrSettingsPoliciesPage(form),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.hrSettingsPoliciesPage() });
      await queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.hrDashboardPage() });
    },
  });
}