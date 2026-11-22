"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  fetchStudentTransferManagementPage,
  saveStudentTransferReview,
} from "@/features/college-admin/api/students";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type {
  StudentTransferManagementPageQuery,
  StudentTransferReviewPayload,
} from "@/features/college-admin/types/student-transfer-management";

export function useStudentTransferManagementPage(params: StudentTransferManagementPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.studentTransferManagementPage(params),
    queryFn: () => fetchStudentTransferManagementPage(params),
  });
}

export function useSaveStudentTransferReview() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: StudentTransferReviewPayload) => saveStudentTransferReview(payload),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: [...collegeAdminQueryKeys.all, "student-transfer-management-page"] });
    },
  });
}