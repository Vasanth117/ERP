"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  cancelStudentWithdrawalDraft,
  fetchStudentWithdrawalDiscontinuationPage,
  saveStudentWithdrawalDraft,
  submitStudentWithdrawalForApproval,
} from "@/features/college-admin/api/students";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type {
  StudentWithdrawalPageQuery,
  StudentWithdrawalSavePayload,
  StudentWithdrawalSubmitPayload,
} from "@/features/college-admin/types/student-withdrawal-discontinuation";

export function useStudentWithdrawalDiscontinuationPage(params: StudentWithdrawalPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.studentWithdrawalDiscontinuationPage(params),
    queryFn: () => fetchStudentWithdrawalDiscontinuationPage(params),
  });
}

export function useSaveStudentWithdrawalDraft() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: StudentWithdrawalSavePayload) => saveStudentWithdrawalDraft(payload),
    onSuccess: () => {
      void client.invalidateQueries({
        queryKey: [...collegeAdminQueryKeys.all, "student-withdrawal-discontinuation-page"],
      });
    },
  });
}

export function useSubmitStudentWithdrawal() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: StudentWithdrawalSubmitPayload) => submitStudentWithdrawalForApproval(payload),
    onSuccess: () => {
      void client.invalidateQueries({
        queryKey: [...collegeAdminQueryKeys.all, "student-withdrawal-discontinuation-page"],
      });
      void client.invalidateQueries({ queryKey: [...collegeAdminQueryKeys.all, "student-status-management-page"] });
    },
  });
}

export function useCancelStudentWithdrawalDraft() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (requestId: string) => cancelStudentWithdrawalDraft(requestId),
    onSuccess: () => {
      void client.invalidateQueries({
        queryKey: [...collegeAdminQueryKeys.all, "student-withdrawal-discontinuation-page"],
      });
    },
  });
}