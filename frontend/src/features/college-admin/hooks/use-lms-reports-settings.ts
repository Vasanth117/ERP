"use client";

import { useQueryClient } from "@tanstack/react-query";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useCollegeAdminMutation as useMutation } from "@/features/college-admin/hooks/use-college-admin-mutation";

import {
  createLmsReportSchedule,
  fetchLmsReportsPage,
  fetchLmsSettingsPage,
  saveLmsSettingsPage,
} from "@/features/college-admin/api/lms-reports-settings";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { LmsReportsPageQuery, LmsSettingsFormValues } from "@/features/college-admin/types/lms-reports-settings";

export function useLmsReportsPage(params?: LmsReportsPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.lmsReportsPage(params),
    queryFn: () => fetchLmsReportsPage(params),
  });
}

export function useCreateLmsReportSchedule(params?: LmsReportsPageQuery) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { report_key: string }) => createLmsReportSchedule(body.report_key, params),
    onSuccess: (data) => {
      queryClient.setQueryData(collegeAdminQueryKeys.lmsReportsPage(params), data);
    },
  });
}

export function useLmsSettingsPage() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.lmsSettingsPage(),
    queryFn: fetchLmsSettingsPage,
  });
}

export function useSaveLmsSettingsPage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (form: LmsSettingsFormValues) => saveLmsSettingsPage(form),
    onSuccess: (data) => {
      queryClient.setQueryData(collegeAdminQueryKeys.lmsSettingsPage(), data);
    },
  });
}