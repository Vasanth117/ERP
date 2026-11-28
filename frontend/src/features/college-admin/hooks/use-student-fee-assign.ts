"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  assignFeeAssessmentsBulk,
  assignFeeAssessmentsGroup,
  createFeeAssessment,
  fetchStudentFeeAssignPage,
} from "@/features/college-admin/api/student-fee-assign";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useStudentFeeAssignPage(enabled = true) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.studentFeeAssignPage(),
    queryFn: fetchStudentFeeAssignPage,
    enabled,
  });
}

export function useAssignStudentFee() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createFeeAssessment,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.studentFeeManagementPage() });
    },
  });
}

export function useAssignStudentFeeGroup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: assignFeeAssessmentsGroup,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.studentFeeManagementPage() });
    },
  });
}

export function useAssignStudentFeeBulk() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: assignFeeAssessmentsBulk,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.studentFeeManagementPage() });
    },
  });
}