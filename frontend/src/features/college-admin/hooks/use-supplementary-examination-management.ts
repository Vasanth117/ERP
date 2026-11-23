"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  createSupplementaryExaminationSession,
  fetchSupplementaryExaminationManagementPage,
} from "@/features/college-admin/api/examinations";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { SupplementaryExaminationManagementPageQuery } from "@/features/college-admin/types/supplementary-examination-management";

export function useSupplementaryExaminationManagementPage(params: SupplementaryExaminationManagementPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.supplementaryExaminationManagementPage(params),
    queryFn: () => fetchSupplementaryExaminationManagementPage(params),
  });
}

export function useCreateSupplementaryExaminationSession() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: createSupplementaryExaminationSession,
    onSuccess: (data, variables) => {
      void client.setQueryData(
        collegeAdminQueryKeys.supplementaryExaminationManagementPage({
          page: variables.page,
          session_id: data.selected_session_id,
        }),
        data,
      );
      void client.invalidateQueries({ queryKey: collegeAdminQueryKeys.all });
    },
  });
}