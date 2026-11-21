"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  approveStudentStatusChange,
  fetchStudentStatusManagementPage,
  submitStudentStatusChange,
} from "@/features/college-admin/api/students";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type {
  StudentStatusApprovePayload,
  StudentStatusChangeSubmitPayload,
  StudentStatusManagementPageQuery,
} from "@/features/college-admin/types/student-status-management";

export function useStudentStatusManagementPage(params: StudentStatusManagementPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.studentStatusManagementPage(params),
    queryFn: () => fetchStudentStatusManagementPage(params),
  });
}

export function useSubmitStudentStatusChange() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: StudentStatusChangeSubmitPayload) => submitStudentStatusChange(payload),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: [...collegeAdminQueryKeys.all, "student-status-management-page"] });
    },
  });
}

export function useApproveStudentStatusChange() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: StudentStatusApprovePayload) => approveStudentStatusChange(payload),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: [...collegeAdminQueryKeys.all, "student-status-management-page"] });
    },
  });
}