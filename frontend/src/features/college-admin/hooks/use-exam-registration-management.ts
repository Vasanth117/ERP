"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  confirmSelectedExamRegistrations,
  fetchExamRegistrationManagementPage,
} from "@/features/college-admin/api/examinations";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { ExamRegistrationManagementPageQuery } from "@/features/college-admin/types/exam-registration-management";

export function useExamRegistrationManagementPage(params: ExamRegistrationManagementPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.examRegistrationManagementPage(params),
    queryFn: () => fetchExamRegistrationManagementPage(params),
  });
}

export function useConfirmSelectedExamRegistrations() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: confirmSelectedExamRegistrations,
    onSuccess: (data, variables) => {
      void client.setQueryData(
        collegeAdminQueryKeys.examRegistrationManagementPage({
          page: variables.page,
          session_id: variables.session_id,
          status: variables.status,
          programme_code: variables.programme_code,
        }),
        data,
      );
      void client.invalidateQueries({ queryKey: collegeAdminQueryKeys.all });
    },
  });
}