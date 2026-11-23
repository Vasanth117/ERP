"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { fetchInternalExternalAssessmentPage, saveInternalExternalAssessment } from "@/features/college-admin/api/examinations";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { InternalExternalAssessmentPageQuery } from "@/features/college-admin/types/internal-external-assessment";

export function useInternalExternalAssessmentPage(params: InternalExternalAssessmentPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.internalExternalAssessmentPage(params),
    queryFn: () => fetchInternalExternalAssessmentPage(params),
  });
}

export function useSaveInternalExternalAssessment() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: saveInternalExternalAssessment,
    onSuccess: (data, variables) => {
      void client.setQueryData(collegeAdminQueryKeys.internalExternalAssessmentPage({ session_id: variables.session_id }), data);
      void client.invalidateQueries({ queryKey: collegeAdminQueryKeys.all });
    },
  });
}