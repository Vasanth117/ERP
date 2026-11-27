import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  fetchAttendanceConfigurationPage,
  fetchAttendanceRulesPoliciesPage,
  saveAttendanceConfiguration,
  saveAttendanceInstitutionalPolicy,
} from "@/features/college-admin/api/attendance-configuration";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type {
  AttendanceConfigurationSavePayload,
  AttendanceInstitutionalPolicySavePayload,
  AttendanceRulesPoliciesQuery,
} from "@/features/college-admin/types/attendance-configuration";

export function useAttendanceConfigurationPage() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.attendanceConfiguration(),
    queryFn: () => fetchAttendanceConfigurationPage(),
  });
}

export function useSaveAttendanceConfiguration() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AttendanceConfigurationSavePayload) => saveAttendanceConfiguration(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.attendanceConfiguration() });
      await queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.attendanceRulesPolicies() });
    },
  });
}

export function useAttendanceRulesPoliciesPage(params?: AttendanceRulesPoliciesQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.attendanceRulesPolicies(params),
    queryFn: () => fetchAttendanceRulesPoliciesPage(params),
  });
}

export function useSaveAttendanceInstitutionalPolicy(params?: AttendanceRulesPoliciesQuery) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AttendanceInstitutionalPolicySavePayload) =>
      saveAttendanceInstitutionalPolicy(payload, params),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.attendanceRulesPolicies(params) });
      await queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.attendanceConfiguration() });
    },
  });
}