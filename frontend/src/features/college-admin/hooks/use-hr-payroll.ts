import { useCollegeAdminMutation as useMutation } from "@/features/college-admin/hooks/use-college-admin-mutation";
import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useQueryClient } from "@tanstack/react-query";

import {
  fetchHrPayrollProcessingPage,
  fetchHrSalarySlipManagementPage,
  fetchHrSalaryStructureManagementPage,
  generateHrSalarySlips,
  processHrPayroll,
  publishHrSalarySlips,
  validateHrPayroll,
} from "@/features/college-admin/api/hr-payroll";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { HrPayrollPageQuery } from "@/features/college-admin/types/hr-payroll";

export function useHrSalaryStructureManagementPage(params?: HrPayrollPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hrSalaryStructureManagementPage(params),
    queryFn: () => fetchHrSalaryStructureManagementPage(params),
  });
}

export function useHrPayrollProcessingPage(params?: HrPayrollPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hrPayrollProcessingPage(params),
    queryFn: () => fetchHrPayrollProcessingPage(params),
  });
}

export function useHrSalarySlipManagementPage(params?: HrPayrollPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hrSalarySlipManagementPage(params),
    queryFn: () => fetchHrSalarySlipManagementPage(params),
  });
}

export function useValidateHrPayroll(payrollRunId?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => validateHrPayroll(payrollRunId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.hrPayrollProcessingPage() });
      await queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.hrSalarySlipManagementPage() });
      await queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.hrDashboardPage() });
    },
  });
}

export function useProcessHrPayroll(payrollRunId?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => processHrPayroll(payrollRunId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.hrPayrollProcessingPage() });
      await queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.hrSalarySlipManagementPage() });
      await queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.hrDashboardPage() });
    },
  });
}

export function useGenerateHrSalarySlips(payrollRunId?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => generateHrSalarySlips(payrollRunId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.hrSalarySlipManagementPage() });
    },
  });
}

export function usePublishHrSalarySlips(payrollRunId?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => publishHrSalarySlips(payrollRunId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.hrSalarySlipManagementPage() });
    },
  });
}